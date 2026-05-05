import logging
import time

def get_logger(nome:str, nivel:str='info', tipo:str='console', caminho:str='log.log'):
    '''
    Cria um objeto logger configurado.
    Args:
        nome(str): Nome do logger.
        nivel(str): Nível limite do resgistrador (debug, info, warning, error ou critical). Padrão: info.
        tipo(str): Tipo de log que será gerado (console ou arquivo). Padrão: console.
    Returns:
        Logger(Logger): Objeto logger configurado.
    '''

    # Cria o Logger
    logger = logging.getLogger(nome)

    # Configura o nível do log conforme definido pelo usuário
    if nivel == 'debug':
        logger.setLevel(logging.DEBUG)
    elif nivel == 'info':
        logger.setLevel(logging.INFO)
    elif nivel == 'warning':
        logger.setLevel(logging.WARNING)
    elif nivel == 'error':
        logger.setLevel(logging.ERROR)
    elif nivel == 'critical':
        logger.setLevel(logging.CRITICAL)
    else:
        # Define o nível como INFO, caso o usuário digite um valor inválido
        logger.setLevel(logging.INFO)


    # Cria o handler
    if not logger.handlers:
        if tipo == 'console':
            # Cria o handler de console
            handler = logging.StreamHandler()
        elif tipo == 'arquivo':
            # Cria o handler de texto
            handler = logging.FileHandler(caminho)
        else:
            # Define o handler de console caso o usuário digite um valor inválido
            handler = logging.StreamHandler()

    # Configura o Formatter para utilizar o fuso horário local
    logging.Formatter.converter = time.localtime

    # Cria o Formatter
    formatter = logging.Formatter(
        fmt='%(asctime)s - %(module)s/%(funcName)s - [%(levelname)s] %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Adiciona o Formatter ao Handler
    handler.setFormatter(formatter)

    # Adiciona o Handler ao Logger
    logger.addHandler(handler)

    return logger