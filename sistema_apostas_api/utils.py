# validation.py
import re

def validar_cpf(cpf: str) -> bool:
    """
    Valida um número de CPF.

    Args:
        cpf (str): O número de CPF a ser validado.

    Returns:
        bool: True se o CPF for válido, False caso contrário.
    """
    cpf = re.sub(r'[^0-9]', '', cpf) # Remove caracteres não numéricos

    if not cpf or len(cpf) != 11:
        return False

    # Verifica se todos os dígitos são iguais (ex: 111.111.111-11)
    if cpf == cpf[0] * 11:
        return False

    # Validação do primeiro dígito verificador
    soma = 0
    for i in range(9):
        soma += int(cpf[i]) * (10 - i)
    resto = 11 - (soma % 11)
    digito1 = 0 if resto > 9 else resto
    if digito1 != int(cpf[9]):
        return False

    # Validação do segundo dígito verificador
    soma = 0
    for i in range(10):
        soma += int(cpf[i]) * (11 - i)
    resto = 11 - (soma % 11)
    digito2 = 0 if resto > 9 else resto
    if digito2 != int(cpf[10]):
        return False

    return True