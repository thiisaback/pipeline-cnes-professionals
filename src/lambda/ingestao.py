from ftplib import FTP, error_perm, error_temp
import os
from urllib.error import URLError
import urllib.request
import boto3
from botocore.exceptions import ClientError

s3_client = boto3.client('s3')

def mapear_arquivos_ftp() -> dict:
    '''
    Cria um dicionário contendo a competência, no formato aamm, dos arquivos mais recentes disponibilizados no módulo 
    Profissionais do CNES, no servidor FTP do DataSUS, bem como uma lista com os nomes dos arquivos dessa competência.

    Returns:
        dict_arquivos(dict): Dicionário com a competência mais recente e a lista de arquivos. 
    '''

    # Identifica o módulo e função atuais para o Log
    funcao_atual = 'ingestao/mapear_arquivos_ftp'

    # Dicionário que armazenará o resultado da função
    dict_arquivos = {}

    # Variáveis de host e diretório
    host = 'ftp.datasus.gov.br'
    dir_pf = 'dissemin/publicos/CNES/200508_/Dados/PF/'

    print(f'[INFO] {funcao_atual} - Iniciando conexão com o servidor {host}')

    try:
        with FTP(host) as servidor:
            
            # Acessa o servidor FTP do DataSUS como usuário anônimo
            servidor.login()
            print(f'[INFO] {funcao_atual} - Conexão estabelecida.')

            # Navega até o diretório que contém as bases de dados
            servidor.cwd(dir_pf)
            print(f'[INFO] {funcao_atual} - Navegando para o diretório {dir_pf}')
            
            # Armazena no dicionário a competência atual dos arquivos do servidor FTP (formato: aamm)
            dict_arquivos['competencia'] = int(servidor.nlst()[-1][-8:-4])
            print(f'[INFO] {funcao_atual} - Competência atual DataSUS: {dict_arquivos['competencia']}')

            # Cria a string de filtragem dos arquivos
            filtro = '*' + str(dict_arquivos['competencia']) + '.dbc'
            print(f'[INFO] {funcao_atual} - String de filtro criada: {filtro}')

            # Armazena no dicionário a lista com os arquivos da competência mais atual do servidor FTP
            dict_arquivos['arquivos'] = servidor.nlst(filtro)
            print(f'[INFO] {funcao_atual} - Resposta DataSUS: {dict_arquivos}')

        return dict_arquivos

    except error_perm as e:
        # Logs de erros de caráter permanente (inexistência de diretórios e/ou arquivos)
        print(f'[ERROR] {funcao_atual} - Falha permanente no servidor FTP: {e}')
        return None

    except error_temp as e:
        # Logs de erros de caráter temporário (instabilidade no servidor)
        print(f'[ERROR] {funcao_atual} - Falha temporária no servidor FTP: {e}')        
        return None

    except Exception as e:
        # Logs de error gerais, armazenando a mensagem completa do erro.
        print(f'[ERROR] {funcao_atual} - Erro: {e}')   
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

    # Identifica o módulo e função atuais para o Log
    funcao_atual = 'ingestao/mapear_arquivos_bucket'    

    dict_arquivos = {}

    # Consulta os arquivos existentes na camada bronze do bucket
    resposta_s3 = s3_client.list_objects_v2(Bucket=bucket, Prefix='bronze/cnes/profissionais/')
    print(f'[INFO] {funcao_atual} - Resposta AWS: {resposta_s3}')
    
    if 'Contents' in resposta_s3:
        
        # Cria uma lista contendo os nomes dos arquivos da camada bronze
        arquivos_bucket = [arquivo['Key'] for arquivo in resposta_s3['Contents']]

        # Identifica a competência dos arquivos na camada bronze
        competencia = arquivos_bucket[-1][-8:-4]
        print(f'[INFO] {funcao_atual} - Competência atual AWS: {competencia}')

        # Insere a competência e a lista com o nome dos arquivos no dicionário
        dict_arquivos['competencia'] = int(competencia)
        dict_arquivos['arquivos'] = arquivos_bucket
    
    else:
        dict_arquivos['competencia'] = 0
        dict_arquivos['arquivos'] = []

    print(f'[INFO] {funcao_atual} - Resposta Data Lake: {dict_arquivos}')

    return dict_arquivos


def transferir_ftp_para_s3(arquivos:list, bucket:str):
    '''
    Transfere os arquivos do CNES Profissionais do servidor FTP do DataSUS para a camada bronze do
    bucket no Amazon S3.

    Args:
        arquivos(list): Lista contendo o nome dos arquivos que serão baixados.
        bucket(str): Nome do bucket de destino no Amazon S3.
    '''

    # Identifica o módulo e função atuais para o Log
    funcao_atual = 'ingestao/transferir_ftp_para_s3' 

    print(f'[INFO] {funcao_atual} - Arquivos para transferir: {arquivos}')

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

                print(f'[INFO] {funcao_atual} - Baixando arquivo: {arquivo}')

                # Nome do arquivo que será armazenado na camada bronze no bucket
                nome_objeto = f'bronze/cnes/profissionais/{arquivo}'

                # Faz o upload do arquivo no bucket do Amazon S3
                s3_client.upload_fileobj(
                    Fileobj=arquivo_path,
                    Bucket=bucket,
                    Key=nome_objeto
                )
                print(f'[INFO] {funcao_atual} - Download concluído: {arquivo}')
                
            # Incrementa a quantidade de downloas realizados
            cont_downloads += 1
                
        except URLError as e:
            # Inclui o nome do arquivo na lista de arquivos que deram erro
            arquivos_erro.append(arquivo)
            print(f'[WARNING] {funcao_atual} - Não foi possível baixar o arquivo {arquivo}: {e}')
            continue

    print(f'[INFO] {funcao_atual} - Transferência concluída. Arquivos baixados: {cont_downloads}/{len(arquivos)}.')

    if cont_downloads != len(arquivos):
        print(f'[INFO] {funcao_atual} - Arquivos não baixados: {arquivos_erro}.')


def excluir_arquivos_bucket(arquivos:list, bucket:str):
    '''
    Exclui os arquivos do bucket no Amazon S3.

    Args:
        arquivos(list): Lista de arquivos a serem excluídos do bucket. 
        bucket(str): Nome do bucket de destino no Amazon S3.
    '''

    # Identifica o módulo e função atuais para o Log
    funcao_atual = 'ingestao/excluir_arquivos_bucket' 

    print(f'[INFO] {funcao_atual} - Arquivos para excluir: {arquivos}')

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
        print(f'[INFO] {funcao_atual} - Arquivos excluídos com sucesso.')

    except ClientError as e:
        print(f'[INFO] {funcao_atual} - Erro ao tentar excluir os arquivos: {e}')


def lambda_handler(event, context):

    # Identifica o módulo e função atuais para o Log
    funcao_atual = 'ingestao' 

    print(f'[INFO] {funcao_atual} - Evento: {event}')
    print(f'[INFO] {funcao_atual} - Contexto: {context}')

    bucket = os.environ.get('S3_BUCKET_NAME')
    print(f'[INFO] {funcao_atual} - Bucket S3 selecionado: {bucket}')

    # # Dicionário com as competências e os arquivos mais atuais disponibilizados no FTP do DataSUS
    resposta_ftp = mapear_arquivos_ftp()

    # # Dicionário com as competências e os arquivos mais atuais disponibilizados no bucket S3
    resposta_aws = mapear_arquivos_bucket(bucket)

    if resposta_aws['competencia'] < resposta_ftp['competencia']:
        
        print(f'[INFO] {funcao_atual} - Os arquivos do Data Lake estão desatualizados.')
        print(f'[INFO] {funcao_atual} - Iniciando a atualização da base de dados no Data Lake...')

        if len(resposta_aws['arquivos']) > 0:
            # Exclui todos os arquivos do bucket
            excluir_arquivos_bucket(resposta_aws['arquivos'], bucket)

        # Atualiza os arquivos da camada Bronze (para fins de teste, está baixando somente 1 arquivo.)
        transferir_ftp_para_s3(resposta_ftp['arquivos'][:1], bucket)
    
    else:
        print(f'[INFO] {funcao_atual} - Os dados do Data Lake já estão atualizados.')

    return {
        'statusCode': 200,
        'body': 'Executado com sucesso!',
        'resposta_ftp': resposta_ftp
    }