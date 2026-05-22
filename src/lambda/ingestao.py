from datetime import datetime
from ftplib import FTP, error_perm, error_temp
import json
import logging
import os
from urllib.error import URLError
import urllib.request
import boto3
from botocore.exceptions import ClientError


def formatar_json(record):
    '''
    Formata os logs para JSON.

    Args:
        record: Objeto LogRecord gerado automaticamente pela biblioteca logging.

    Returns:
        log(str): Log formatado no modelo de JSON, como string.
    '''

    log_dict = {
        'timestamp': datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S'),
        'type': 'process',
        'level': record.levelname,
        'service': 'AWS Lambda',
        'module': os.environ.get('AWS_LAMBDA_FUNCTION_NAME'),
        'function': record.funcName,
        'message': record.getMessage()
    }

    return json.dumps(log_dict, ensure_ascii=False)


def logger_config(nome:str):
    '''
    Instancia e configura o logger.

    Args:
        nome(str): Nome do logger.
    
    Returns:
        Logger: Objeto logger configurado.
    '''

    logger = logging.getLogger(nome)
    logger.setLevel(logging.INFO)
    logger.propagate = False

    # Formatter
    formatter = logging.Formatter(datefmt='%d/%m/%Y %H:%M:%S')
    formatter.format = formatar_json

    # Handler de terminal
    handler = logging.StreamHandler()

    # Adiciona o formato ao handler
    handler.setFormatter(formatter)

    # Adicionando o handler no logger
    if not logger.handlers:
        logger.addHandler(handler)

    return logger


def instanciar_client(servico:str):
    '''
    Instancia o serviço da AWS informado.

    Args:
        servico(str): Nome do serviço, conforme nomenclatura utilizada no boto3.

    Returns:
        client: Cliente do serviço da AWS.
    '''

    logger.info('Instanciando cliente S3...')
    client = boto3.client(servico)
    logger.info('Instância criada com sucesso.')

    return client


# Configura o logger
logger = logger_config('PipeSUS')

# Instancia o cliente do S3
s3_client = instanciar_client('s3')


def mapear_arquivos_ftp() -> dict:
    '''
    Cria um dicionário contendo a competência, no formato aamm, dos arquivos mais recentes disponibilizados no módulo 
    Profissionais do CNES, no servidor FTP do DataSUS, bem como uma lista com os nomes dos arquivos dessa competência.

    Returns:
        dict_arquivos(dict): Dicionário com a competência mais recente e a lista de arquivos. 
    '''

    # Dicionário que armazenará o resultado da função
    dict_arquivos = {}

    # Variáveis de host e diretório
    host = 'ftp.datasus.gov.br'
    dir_pf = 'dissemin/publicos/CNES/200508_/Dados/PF/'

    logger.info(f'Iniciando conexão com o servidor {host}')

    try:
        with FTP(host) as servidor:
            
            # Acessa o servidor FTP do DataSUS como usuário anônimo
            servidor.login()
            logger.info('Conexão estabelecida.')

            # Navega até o diretório que contém as bases de dados
            servidor.cwd(dir_pf)
            logger.info(f'Navegando para o diretório {dir_pf}')
            
            # Armazena no dicionário a competência atual dos arquivos do servidor FTP (formato: aamm)
            dict_arquivos['competencia'] = int(servidor.nlst()[-1][-8:-4])
            logger.info(f'Competência atual DataSUS: {dict_arquivos['competencia']}')

            # Cria a string de filtragem dos arquivos
            filtro = '*' + str(dict_arquivos['competencia']) + '.dbc'
            logger.info(f'String de filtro criada: {filtro}')

            # Armazena no dicionário a lista com os arquivos da competência mais atual do servidor FTP
            dict_arquivos['arquivos'] = servidor.nlst(filtro)
            logger.info(f'Resposta DataSUS: {dict_arquivos}')

        return dict_arquivos

    except error_perm as e:
        # Logs de erros de caráter permanente (inexistência de diretórios e/ou arquivos)
        logger.error(f'Falha permanente no servidor FTP: {e}')
        return None

    except error_temp as e:
        # Logs de erros de caráter temporário (instabilidade no servidor)
        logger.error(f'Falha temporária no servidor FTP: {e}')     
        return None

    except Exception as e:
        # Logs de error gerais, armazenando a mensagem completa do erro.
        logger.error(f'Erro: {e}')
        return None


def mapear_arquivos_bucket(bucket:str) -> dict:
    '''
    Cria um dicionário contendo a competência, no formato aamm, dos arquivos mais recentes disponibilizados no bucket 
    do Amazon S3, bem como uma lista com o nome dos arquivos dessa competência.

    Args:
        bucket(str): Nome do bucket de destino no Amazon S3.

    Returns:
        dict_arquivos(dict): Dicionário com a competência mais recente e a lista de arquivos. 
    '''

    dict_arquivos = {}

    # Consulta os arquivos existentes na camada bronze do bucket
    resposta_s3 = s3_client.list_objects_v2(Bucket=bucket, Prefix='bronze/cnes/profissionais/')
    logger.info(f'Resposta AWS: {resposta_s3}')
    
    if 'Contents' in resposta_s3:
        
        # Cria uma lista contendo os nomes dos arquivos da camada bronze
        arquivos_bucket = [arquivo['Key'] for arquivo in resposta_s3['Contents']]

        # Identifica a competência dos arquivos na camada bronze
        competencia = arquivos_bucket[-1][-8:-4]
        logger.info(f'Competência atual AWS: {competencia}')

        # Insere a competência e a lista com o nome dos arquivos no dicionário
        dict_arquivos['competencia'] = int(competencia)
        dict_arquivos['arquivos'] = arquivos_bucket
    
    else:
        dict_arquivos['competencia'] = 0
        dict_arquivos['arquivos'] = []

    logger.info(f'Resposta Data Lake: {dict_arquivos}')

    return dict_arquivos


def comparar_competencias(arquivos_ftp:dict, arquivos_aws:dict) -> bool:
    '''
    Compara as competências dos arquivos do DataSUS e do Data Lake na AWS.

    Args:
        arquivos_ftp(dict): Dicionário contendo a competência e os arquivos do DataSUS.
        arquivos_aws(dict): Dicionário contendo a competência e os arquivos do Data Lake na AWS.
    
    Returns:
        atualizado(bool): Retorna True se o Data Lake estiver atualizado e False se estiver desatualizado.
    '''

    if arquivos_aws['competencia'] < arquivos_ftp['competencia']:
        logger.info('Os arquivos do Data Lake estão desatualizados.')
        return False
    
    else:
        logger.info('Os dados do Data Lake já estão atualizados.')
        return True


def transferir_ftp_para_s3(arquivos:list, bucket:str):
    '''
    Transfere os arquivos do CNES Profissionais do servidor FTP do DataSUS para a camada bronze do
    bucket no Amazon S3.

    Args:
        arquivos(list): Lista contendo o nome dos arquivos que serão baixados.
        bucket(str): Nome do bucket de destino no Amazon S3.
    '''

    logger.info(f'Arquivos para transferir: {arquivos}')

    # URL base do servidor FTP
    url_ftp = 'ftp://ftp.datasus.gov.br/dissemin/publicos/CNES/200508_/Dados/PF'

    # Contabiliza a quantidade de arquivos baixados
    cont_downloads = 0

    # Cria uma lista de arquivos que não tiveram a transferência concluída para o S3
    arquivos_erro = []

    # Realiza o download de cada arquivo da lista arquivos
    for arquivo in arquivos:

        try:
            # Cria uma requisição HTTPS para baixar o arquivo
            with urllib.request.urlopen(f'{url_ftp}/{arquivo}') as arquivo_path:

                logger.info(f'Baixando arquivo: {arquivo}')

                # Nome do arquivo que será armazenado na camada bronze no bucket
                nome_objeto = f'bronze/cnes/profissionais/{arquivo}'

                # Faz o upload do arquivo no bucket do Amazon S3
                s3_client.upload_fileobj(
                    Fileobj=arquivo_path,
                    Bucket=bucket,
                    Key=nome_objeto
                )
                logger.info(f'Download concluído: {arquivo}')
                
            # Incrementa a quantidade de downloas realizados
            cont_downloads += 1
                
        except URLError as e:
            # Inclui o nome do arquivo na lista de arquivos que deram erro
            arquivos_erro.append(arquivo)
            logger.warning(f'Não foi possível baixar o arquivo {arquivo}: {e}')
            continue

    logger.info(f'Transferência concluída. Arquivos baixados: {cont_downloads}/{len(arquivos)}.')

    if cont_downloads != len(arquivos):
        logger.info(f'Arquivos não baixados: {arquivos_erro}.')


def excluir_arquivos_bucket(arquivos:list, bucket:str):
    '''
    Exclui os arquivos do bucket no Amazon S3.

    Args:
        arquivos(list): Lista de arquivos a serem excluídos do bucket. 
        bucket(str): Nome do bucket de destino no Amazon S3.
    '''

    logger.info(f'Arquivos para excluir: {arquivos}')

    # Cria uma lista de dicionários dos arquivos a serem excluídos
    arquivos_deletar = [{'Key': arquivo} for arquivo in arquivos]

    try:
        # Exclui os arquivos do bucket
        s3_client.delete_objects(
            Bucket=bucket,
            Delete={
                'Objects': arquivos_deletar,
                'Quiet': True
            }
        )
        logger.info('Arquivos excluídos com sucesso.')

    except ClientError as e:
        logger.error(f'Erro ao tentar excluir os arquivos: {e}')


def atualizar_data_lake(bucket:str, arquivos_ftp:dict, arquivos_aws:dict):
    '''
    Atualiza o Data Lake na AWS com os dados da competência mais recente do DataSUS.

    Args:
        bucket(str): Nome do bucket de destino no Amazon S3.
        arquivos_ftp(dict): Dicionário contendo a competência e os arquivos do DataSUS.
        arquivos_aws(dict): Dicionário contendo a competência e os arquivos do Data Lake na AWS.
    '''
    logger.info('Iniciando a atualização da base de dados no Data Lake...')

    if len(arquivos_aws['arquivos']) > 0:
        # Exclui todos os arquivos do bucket
        excluir_arquivos_bucket(arquivos_aws['arquivos'], bucket)

    # Atualiza os arquivos da camada Bronze (para fins de teste, está baixando somente 1 arquivo.)
    transferir_ftp_para_s3(arquivos_ftp['arquivos'][:1], bucket)


def lambda_handler(event, context):

    logger.info(f'Evento: {event}')
    logger.info(f'Contexto: {context}')

    bucket = os.environ.get('S3_BUCKET_NAME')
    logger.info(f'Bucket S3 selecionado: {bucket}')

    # Dicionário com as competências e os arquivos mais atuais disponibilizados no FTP do DataSUS
    resposta_ftp = mapear_arquivos_ftp()

    # Dicionário com as competências e os arquivos mais atuais disponibilizados no bucket S3
    resposta_aws = mapear_arquivos_bucket(bucket)

    # Verifica se o Data Lake (AWS) está atualizado
    atualizado = comparar_competencias(resposta_ftp, resposta_aws)

    if atualizado == False:
        # Atualiza os dados do Data Lake
        atualizar_data_lake(bucket, resposta_ftp, resposta_aws)
    
    return {
        'statusCode': 200,
        'body': 'Executado com sucesso!',
        'resposta_ftp': resposta_ftp
    }