from datetime import datetime
from ftplib import FTP, error_perm, error_temp
import os
from urllib.error import URLError
import urllib.request
import boto3
from botocore.exceptions import ClientError
from dotenv import load_dotenv
from src.utils.logger import get_logger


# --------------------------
# CONFIGURAÇÕES INICIAIS
# --------------------------

# Define a data e hora de execução
date_time = datetime.now().strftime('%Y-%m-%d %H-%M-%S')

# Define os nomes completos dos arquivos de log de processos e de métricas
log_process_filename = os.path.join('logs/process', f'process_log_{date_time}.log')
log_metrics_filename = os.path.join('logs/metrics', f'metrics_log_{date_time}.log')

# Cria os objetos logger de processos e de métricas, bem como o objeto logger de console
logger_console = get_logger('ingest')
logger_process = get_logger('ingest_process',nivel='debug',tipo='arquivo',caminho=log_process_filename)
#logger_metrics = get_logger('ingest_metrics',nivel='info',tipo='arquivo',caminho=log_metrics_filename) # Será implementado

# Carrega as variáveis do arquivo .env para o ambiente
load_dotenv()

# Define a região e o bucket padrões, conforme informado no .env
regiao = os.getenv('AWS_DEFAULT_REGION')
bucket = os.getenv('S3_BUCKET_NAME')

# Cria o client para o Amazon S3
try:
    s3_client = boto3.client('s3', region_name=regiao)

except ClientError as e:
    logger_console.error(f'Não foi possível criar o client: {e}')


# --------------------------
# FUNÇÕES
# --------------------------

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

    logger_console.info(f'Iniciando conexão com o servidor {host}')
    logger_process.info(f'Iniciando conexão com o servidor {host}')

    try:
        with FTP(host) as servidor:
            
            # Acessa o servidor FTP do DataSUS como usuário anônimo
            servidor.login()
            logger_console.info(f'Conectado ao servidor {host}')
            logger_process.info(f'Conectado ao servidor {host}')

            # Navega até o diretório que contém as bases de dados
            servidor.cwd(dir_pf)
            logger_console.info(f'Navegando para o diretório {dir_pf}')
            logger_process.info(f'Navegando para o diretório {dir_pf}')
            
            # Armazena no dicionário a competência atual dos arquivos do servidor FTP (formato: aamm)
            logger_process.info(f'Identificando competência atual dos arquivos do servidor FTP...')
            dict_arquivos['competencia'] = int(servidor.nlst()[-1][-8:-4])
            logger_process.info(f'Competência atual (FTP): {dict_arquivos['competencia']}')

            # Cria a string de filtragem dos arquivos
            filtro = '*' + str(dict_arquivos['competencia']) + '.dbc'
            logger_process.info(f'String de filtro criada: {filtro}')

            # Armazena no dicionário a lista com os arquivos da competência mais atual do servidor FTP
            dict_arquivos['arquivos'] = servidor.nlst(filtro)
            logger_console.info(
                f'Arquivos identificados da competência {str(dict_arquivos['competencia'])[-2:]}/{str(dict_arquivos['competencia'])[:2]}: \
                {len(dict_arquivos['arquivos'])} arquivo(s).'
            )
            logger_process.info(
                f'Arquivos identificados da competência {str(dict_arquivos['competencia'])[-2:]}/{str(dict_arquivos['competencia'])[:2]}: \
                {len(dict_arquivos['arquivos'])} arquivo(s).'
            )
            logger_process.info(f'Arquivos: {dict_arquivos['arquivos']}')

        return dict_arquivos

    except error_perm as e:
        # Logs de erros de caráter permanente (inexistência de diretórios e/ou arquivos)
        logger_console.error(f'Falha permanente no servidor FTP. Consulte o log de processo para mais detalhes.')
        logger_process.error(f'Falha permanente no servidor FTP: {e}')
        return None

    except error_temp as e:
        # Logs de erros de caráter temporário (instabilidade no servidor)
        logger_console.error(f'Falha temporária no servidor FTP. Consulte o log de processo para mais detalhes.')
        logger_process.error(f'Falha temporária no servidor FTP: {e}')        
        return None

    except Exception as e:
        # Logs de error gerais, armazenando a mensagem completa do erro.
        logger_console.error(f'Ocorreu um erro na execução. Consulte o log de processo para mais detalhes.')
        logger_process.error(f'Erro: {e}')   
        return None


def verificar_bucket(bucket:str)->bool:
    '''
    Verifica se o bucket informado existe no Amazon S3.

    Args:
        bucket(str): Nome do bucket no Amazon S3.

    Returns:
        existe(bool): Retorna True se o bucket existir e False se não existir.
    '''
    logger_console.info('Solicitando lista de buckets ao servidor do Amazon S3...')
    logger_process.info('Solicitando lista de buckets ao servidor do Amazon S3...')

    # Retorna os metadados dos buckets no Amazon S3
    resposta_s3 = s3_client.list_buckets()
    logger_process.info(f'Resposta Amazon S3: {resposta_s3}')
    
    # Cria uma lista com os nomes dos buckets existentes
    lista_buckets = [bucket_s3['Name'] for bucket_s3 in resposta_s3['Buckets']]
    logger_process.info(f'Buckets: {lista_buckets}')
    
    if bucket in lista_buckets:
        logger_console.info(f'Bucket {bucket} localizado.')
        logger_process.info(f'Bucket {bucket} localizado.')
        return True
    else:
        logger_console.info(f'Bucket {bucket} não encontrado.')
        logger_process.info(f'Bucket {bucket} não encontrado.')
        return False


def criar_bucket(bucket:str, regiao:str=regiao)->bool:
    '''
    Cria um bucket no Amazon S3.

    Args:
        bucket(str): Nome do bucket que será criado.
        regiao(str): Região em que o bucket será criado. Padrão: Região informada o .env.

    Returns:
        criado(bool): Retorna True se o bucket foi criado e False se não foi criado.
    '''

    try:                    
        # Cria o bucket na região especificada no .env
        if regiao == 'us-east-1':
            resposta_s3 = s3_client.create_bucket(Bucket=bucket)

        else:
            resposta_s3 = s3_client.create_bucket(
                Bucket=bucket,
                CreateBucketConfiguration={
                    'LocationConstraint': regiao
                }
            )

            logger_console.info(f'Bucket {bucket} criado com sucesso.')
            logger_process.info(f'Bucket {bucket} criado com sucesso.')
            criado = True
            return criado

    except ClientError as e:
            logger_console.error(f'Erro ao criar o bucket {bucket}. Consulte o log de processo para mais detalhes.')
            logger_process.error(f'Erro ao criar o bucket {bucket}: {e}')
            criado = False
            return criado


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

    logger_process.info(f'Solicitando lista de arquivos da camada bronze do bucket {bucket} ao servidor do Amazon S3...')

    # Consulta os arquivos existentes na camada bronze do bucket
    resposta_s3 = s3_client.list_objects_v2(Bucket=bucket, Prefix='bronze/cnes/profissionais/')
    logger_process.info(resposta_s3)
    
    if 'Contents' in resposta_s3:
        
        # Cria uma lista contendo os nomes dos arquivos da camada bronze
        arquivos_bucket = [arquivo['Key'] for arquivo in resposta_s3['Contents']]

        # Identifica a competência dos arquivos na camada bronze
        competencia = arquivos_bucket[-1][-8:-4]
        logger_process.info(f'Competência atual (bucket): {competencia}')

        # Insere a competência e a lista com o nome dos arquivos no dicionário
        dict_arquivos['competencia'] = int(competencia)
        dict_arquivos['arquivos'] = arquivos_bucket
        logger_process.info(
            f'Arquivos identificados da competência {str(dict_arquivos['competencia'])[-2:]}/{str(dict_arquivos['competencia'])[:2]}: \
            {len(dict_arquivos['arquivos'])} arquivo(s).'
        )
        logger_process.info(f'Arquivos: {dict_arquivos['arquivos']}')
    
    else:
        dict_arquivos['competencia'] = 0
        dict_arquivos['arquivos'] = []
        logger_console.info(f'Não foram encontrados arquivos na camada bronze do bucket {bucket}.')
        logger_process.info(f'Não foram encontrados arquivos na camada bronze do bucket {bucket}.')

    return dict_arquivos


def excluir_arquivos_bucket(arquivos:list, bucket:str):
    '''
    Exclui os arquivos do bucket no Amazon S3.

    Args:
        arquivos(listt): Lista de arquivos a serem excluídos do bucket. 
        bucket(str): Nome do bucket de destino no Amazon S3.
    '''

    # Cria uma lista de dicionários dos arquivos a serem excluídos
    arquivos_deletar = [{'Key': arquivo} for arquivo in arquivos]
    logger_process.info(f'Foram identificados {len(arquivos_deletar)} arquivos para serem excluídos do bucket {bucket}.')
    logger_process.info(f'Arquivos para serem excluídos do bucket: {arquivos_deletar}')

    try:
        # Exclui os arquivos do bucket
        s3_client.delete_objects(
            Bucket=bucket,
            Delete={
                'Objects': arquivos_deletar,
                'Quiet': True
            }
        )
            
        logger_console.info(f'{len(arquivos_deletar)} arquivos foram excluídos.')
        logger_process.info(f'{len(arquivos_deletar)} arquivos foram excluídos.')

    except ClientError as e:
        logger_console.error(f'Erro ao tentar excluir os arquivos. Consulte o log de processo para mais detalhes.')
        logger_process.error(f'Erro ao tentar excluir os arquivos: {e}')



def transferir_ftp_para_s3(arquivos:list, bucket:str):
    '''
    Transfere os arquivos do CNES Profissionais do servidor FTP do DataSUS para a camada bronze do
    bucket no Amazon S3.

    Args:
        arquivos(list): Lista contendo o nome dos arquivos que serão baixados.
        bucket(str): Nome do bucket de destino no Amazon S3.
    '''

    logger_process.info(f'Arquivos para baixar: {arquivos}')

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

                logger_process.info(f'Baixando arquivo: {arquivo}')

                # Nome do arquivo que será armazenado na camada bronze no bucket
                nome_objeto = f'bronze/cnes/profissionais/{arquivo}'

                # Faz o upload do arquivo no bucket do Amazon S3
                s3_client.upload_fileobj(
                    Fileobj=arquivo_path,
                    Bucket=bucket,
                    Key=nome_objeto
                )
                logger_process.info(f'Download concluído: {arquivo}')
            
            cont_downloads += 1

        except URLError as e:
            # Inclui o nome do arquivo na lista de arquivos que deram erro
            arquivos_erro.append(arquivo)

            logger_console.warning(f'Não foi possível baixar o arquivo {arquivo}.')
            logger_process.warning(f'Não foi possível baixar o arquivo {arquivo}: {e}')
            continue

    logger_console.info(f'Transferência concluída. Arquivos baixados: {cont_downloads}/{len(arquivos)}.')
    logger_process.info(f'Transferência concluída. Arquivos baixados: {cont_downloads}/{len(arquivos)}.')

    if cont_downloads != len(arquivos):
        logger_console.warning(f'Arquivos não baixados: {arquivos_erro}.')
        logger_process.warning(f'Arquivos não baixados: {arquivos_erro}.')


def processar_ingestao():

    logger_console.info('Iniciando pipeline de ingestão CNES.')
    logger_process.info('Iniciando pipeline de ingestão CNES.')
    logger_process.info(f'Bucket: {bucket} | Região: {regiao}')

    # Dicionário com a competência atual e nomes dos arquivos do CNES Profissionais do servidor FTP do DataSUS
    dict_arquivos_ftp = mapear_arquivos_ftp()

    if dict_arquivos_ftp == None:
        logger_console.warning('A consulta não retornou arquivos do servidor FTP.')
        logger_process.warning('A consulta não retornou arquivos do servidor FTP.')

    else:
        logger_console.info(f'Verificando existência do bucket {bucket} no Amazon S3.')
        logger_process.info(f'Verificando existência do bucket {bucket} no Amazon S3.')

        # Verifica se o bucket existe no Amazon S3
        bucket_existe = verificar_bucket(bucket)

        if bucket_existe == False:
            logger_console.info(f'Criando o bucket {bucket} na região {regiao}.')
            logger_process.info(f'Criando o bucket {bucket} na região {regiao}.')

            # Cria o bucket, caso não exista no Amazon S3
            bucket_criado = criar_bucket(bucket, regiao)

        else:
            # Armazena que o bucket não precisou ser criado
            bucket_criado = False

        if bucket_criado == True or bucket_existe == True:
            logger_console.info(f'Mapeando arquivos do bucket {bucket}.')
            logger_process.info(f'Mapeando arquivos do bucket {bucket}.')

            # Dicionário com a competência atual e nomes dos arquivos do bucket no Amazon S3
            dict_arquivos_bucket = mapear_arquivos_bucket(bucket)

            logger_process.info(f'Comparando competências do FTP e do bucket...')
            logger_process.info(f'Competência FTP: {dict_arquivos_ftp['competencia']} | Competência bucket: {dict_arquivos_bucket['competencia']}')

            if dict_arquivos_ftp['competencia'] > dict_arquivos_bucket['competencia']:
                logger_console.info(f'Os arquivos do bucket estão desatualizados. Iniciando atualização...')
                logger_process.info(f'Os arquivos do bucket estão desatualizados. Iniciando atualização...')

                if len(dict_arquivos_bucket['arquivos']) > 0:
                    logger_console.info(f'Excluindo arquivos antigos...')
                    logger_process.info(f'Excluindo arquivos antigos...')

                    # Exclui os arquivos desatualizados do bucket, se houver
                    excluir_arquivos_bucket(dict_arquivos_bucket['arquivos'], bucket=bucket)

                logger_console.info('Iniciando a transferência dos arquivos atualizados...')
                logger_process.info('Iniciando a transferência dos arquivos atualizados...')

                # Transfere os arquivos do servidor FTP do DataSUS para o bucket no Amazon S3.
                transferir_ftp_para_s3(dict_arquivos_ftp['arquivos'], bucket=bucket)
            
            else:
                logger_console.info('Os dados já estão atualizados.')
                logger_process.info('Os dados já estão atualizados.')
    
    logger_console.info('Pipeline de ingestão concluída.')
    logger_process.info('Pipeline de ingestão concluída.')