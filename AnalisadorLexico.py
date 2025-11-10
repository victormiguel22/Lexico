import re
from enum import Enum
from dataclasses import dataclass
from typing import List, Optional

class TokenType(Enum):
    # Palavras reservadas
    SE = "SE"
    SENAO = "SENAO"
    PARA = "PARA"
    FACA = "FACA"
    ENQUANTO = "ENQUANTO"
    ESCREVA = "ESCREVA"
    LEIA = "LEIA"
    INTEIRO = "INTEIRO"
    FLUTUANTE = "FLUTUANTE"
    LOGICO = "LOGICO"
    CADEIA = "CADEIA"
    INICIO = "INICIO"
    FIM = "FIM"
    
    # Identificadores e constantes
    IDENTIFICADOR = "IDENTIFICADOR"
    CONST_INTEIRO = "CONST_INTEIRO"
    CONST_FLOAT = "CONST_FLOAT"
    CONST_STRING = "CONST_STRING"
    CONST_BOOL = "CONST_BOOL"
    
    # Operadores
    ADICAO = "ADICAO"
    SUBTRACAO = "SUBTRACAO"
    MULTIPLICACAO = "MULTIPLICACAO"
    DIVISAO = "DIVISAO"
    MAIOR = "MAIOR"
    MENOR = "MENOR"
    MAIOR_IGUAL = "MAIOR_IGUAL"
    MENOR_IGUAL = "MENOR_IGUAL"
    ATRIBUICAO = "ATRIBUICAO"
    CONCATENACAO = "CONCATENACAO"
    INCREMENTO = "INCREMENTO"
    DECREMENTO = "DECREMENTO"
    
    # Delimitadores
    ABRE_PAREN = "ABRE_PAREN"
    FECHA_PAREN = "FECHA_PAREN"
    ABRE_COLCHETE = "ABRE_COLCHETE"
    FECHA_COLCHETE = "FECHA_COLCHETE"
    
    # Especiais
    EOF = "EOF"

@dataclass
class Token:
    tipo: TokenType
    lexema: str
    linha: int
    coluna: int
    
    def __str__(self):
        return f"Token({self.tipo.value}, '{self.lexema}', linha={self.linha}, coluna={self.coluna})"

@dataclass
class ErroLexico:
    mensagem: str
    linha: int
    coluna: int
    
    def __str__(self):
        return f"Erro léxico [linha {self.linha}, coluna {self.coluna}]: {self.mensagem}"

class AnalisadorLexico:
    def __init__(self, codigo_fonte: str):
        self.codigo = codigo_fonte
        self.posicao = 0
        self.linha = 1
        self.coluna = 1
        self.tokens: List[Token] = []
        self.erros: List[ErroLexico] = []
        
        # Palavras reservadas
        self.palavras_reservadas = {
            'se': TokenType.SE,
            'senao': TokenType.SENAO,
            'para': TokenType.PARA,
            'faca': TokenType.FACA,
            'enquanto': TokenType.ENQUANTO,
            'escreva': TokenType.ESCREVA,
            'leia': TokenType.LEIA,
            'inteiro': TokenType.INTEIRO,
            'flutuante': TokenType.FLUTUANTE,
            'logico': TokenType.LOGICO,
            'cadeia': TokenType.CADEIA,
            'inicio': TokenType.INICIO,
            'fim': TokenType.FIM,
            'verdadeiro': TokenType.CONST_BOOL,
            'falso': TokenType.CONST_BOOL,
        }
    
    def caractere_atual(self) -> Optional[str]:
        """Retorna o caractere atual ou None se fim do arquivo"""
        if self.posicao >= len(self.codigo):
            return None
        return self.codigo[self.posicao]
    
    def proximo_caractere(self) -> Optional[str]:
        """Retorna o próximo caractere sem avançar"""
        if self.posicao + 1 >= len(self.codigo):
            return None
        return self.codigo[self.posicao + 1]
    
    def avancar(self):
        """Avança para o próximo caractere"""
        if self.posicao < len(self.codigo):
            if self.codigo[self.posicao] == '\n':
                self.linha += 1
                self.coluna = 1
            else:
                self.coluna += 1
            self.posicao += 1
    
    def pular_espacos(self):
        """Pula espaços em branco"""
        while self.caractere_atual() and self.caractere_atual() in ' \t\n\r':
            self.avancar()
    
    def pular_comentario(self):
        """Pula comentários de linha (//) e bloco (/* */)"""
        char = self.caractere_atual()
        prox = self.proximo_caractere()
        
        # Comentário de linha //
        if char == '/' and prox == '/':
            while self.caractere_atual() and self.caractere_atual() != '\n':
                self.avancar()
            if self.caractere_atual() == '\n':
                self.avancar()
            return True
        
        # Comentário de bloco /* */
        if char == '/' and prox == '*':
            linha_inicio = self.linha
            coluna_inicio = self.coluna
            self.avancar()  # pula /
            self.avancar()  # pula *
            
            while self.caractere_atual():
                if self.caractere_atual() == '*' and self.proximo_caractere() == '/':
                    self.avancar()  # pula *
                    self.avancar()  # pula /
                    return True
                self.avancar()
            
            # Comentário não fechado
            self.erros.append(ErroLexico(
                "Comentário de bloco não fechado",
                linha_inicio,
                coluna_inicio
            ))
            return True
        
        return False
    
    def ler_numero(self) -> Token:
        """Lê um número inteiro ou float"""
        linha_inicio = self.linha
        coluna_inicio = self.coluna
        numero = ""
        eh_float = False
        
        while self.caractere_atual() and (self.caractere_atual().isdigit() or self.caractere_atual() == '.'):
            if self.caractere_atual() == '.':
                if eh_float:
                    # Segundo ponto encontrado - erro
                    self.erros.append(ErroLexico(
                        f"Número mal formado: '{numero + self.caractere_atual()}'",
                        linha_inicio,
                        coluna_inicio
                    ))
                    self.avancar()
                    break
                eh_float = True
            numero += self.caractere_atual()
            self.avancar()
        
        # Verifica se termina com ponto
        if numero.endswith('.'):
            self.erros.append(ErroLexico(
                f"Número mal formado: '{numero}'",
                linha_inicio,
                coluna_inicio
            ))
        
        tipo = TokenType.CONST_FLOAT if eh_float else TokenType.CONST_INTEIRO
        return Token(tipo, numero, linha_inicio, coluna_inicio)
    
    def ler_identificador(self) -> Token:
        """Lê um identificador ou palavra reservada"""
        linha_inicio = self.linha
        coluna_inicio = self.coluna
        identificador = ""
        
        # Primeiro caractere deve ser letra ou underscore
        while self.caractere_atual() and (self.caractere_atual().isalnum() or self.caractere_atual() == '_'):
            identificador += self.caractere_atual()
            self.avancar()
        
        # Verifica se é palavra reservada
        identificador_lower = identificador.lower()
        if identificador_lower in self.palavras_reservadas:
            tipo = self.palavras_reservadas[identificador_lower]
        else:
            tipo = TokenType.IDENTIFICADOR
        
        return Token(tipo, identificador, linha_inicio, coluna_inicio)
    
    def ler_string(self) -> Token:
        """Lê uma cadeia de caracteres entre aspas"""
        linha_inicio = self.linha
        coluna_inicio = self.coluna
        string = ""
        aspas = self.caractere_atual()  # " ou '
        
        self.avancar()  # pula aspas inicial
        
        while self.caractere_atual() and self.caractere_atual() != aspas:
            if self.caractere_atual() == '\n':
                self.erros.append(ErroLexico(
                    "String não fechada antes do fim da linha",
                    linha_inicio,
                    coluna_inicio
                ))
                break
            
            # Tratamento de escape
            if self.caractere_atual() == '\\' and self.proximo_caractere():
                self.avancar()
                char_escape = self.caractere_atual()
                if char_escape == 'n':
                    string += '\n'
                elif char_escape == 't':
                    string += '\t'
                elif char_escape == '\\':
                    string += '\\'
                elif char_escape == '"':
                    string += '"'
                elif char_escape == "'":
                    string += "'"
                else:
                    string += char_escape
                self.avancar()
            else:
                string += self.caractere_atual()
                self.avancar()
        
        if self.caractere_atual() == aspas:
            self.avancar()  # pula aspas final
        else:
            self.erros.append(ErroLexico(
                "String não fechada",
                linha_inicio,
                coluna_inicio
            ))
        
        return Token(TokenType.CONST_STRING, string, linha_inicio, coluna_inicio)
    
    def proximo_token(self) -> Optional[Token]:
        """Retorna o próximo token do código fonte"""
        # Pula espaços e comentários
        while True:
            self.pular_espacos()
            if not self.pular_comentario():
                break
        
        char = self.caractere_atual()
        
        # Fim do arquivo
        if char is None:
            return Token(TokenType.EOF, "", self.linha, self.coluna)
        
        linha_inicio = self.linha
        coluna_inicio = self.coluna
        
        # Números
        if char.isdigit():
            return self.ler_numero()
        
        # Identificadores e palavras reservadas
        if char.isalpha() or char == '_':
            return self.ler_identificador()
        
        # Strings
        if char in '"\'':
            return self.ler_string()
        
        # Operadores de dois caracteres
        prox = self.proximo_caractere()
        
        # ++
        if char == '+' and prox == '+':
            self.avancar()
            self.avancar()
            return Token(TokenType.INCREMENTO, "++", linha_inicio, coluna_inicio)
        
        # --
        if char == '-' and prox == '-':
            self.avancar()
            self.avancar()
            return Token(TokenType.DECREMENTO, "--", linha_inicio, coluna_inicio)
        
        # >=
        if char == '>' and prox == '=':
            self.avancar()
            self.avancar()
            return Token(TokenType.MAIOR_IGUAL, ">=", linha_inicio, coluna_inicio)
        
        # <=
        if char == '<' and prox == '=':
            self.avancar()
            self.avancar()
            return Token(TokenType.MENOR_IGUAL, "<=", linha_inicio, coluna_inicio)
        
        # :=
        if char == ':' and prox == '=':
            self.avancar()
            self.avancar()
            return Token(TokenType.ATRIBUICAO, ":=", linha_inicio, coluna_inicio)
        
        # &
        if char == '&':
            self.avancar()
            return Token(TokenType.CONCATENACAO, "&", linha_inicio, coluna_inicio)
        
        # Operadores de um caractere
        operadores_simples = {
            '+': TokenType.ADICAO,
            '-': TokenType.SUBTRACAO,
            '*': TokenType.MULTIPLICACAO,
            '/': TokenType.DIVISAO,
            '>': TokenType.MAIOR,
            '<': TokenType.MENOR,
            '(': TokenType.ABRE_PAREN,
            ')': TokenType.FECHA_PAREN,
            '[': TokenType.ABRE_COLCHETE,
            ']': TokenType.FECHA_COLCHETE,
        }
        
        if char in operadores_simples:
            self.avancar()
            return Token(operadores_simples[char], char, linha_inicio, coluna_inicio)
        
        # Caractere inválido
        self.erros.append(ErroLexico(
            f"Caractere inválido: '{char}'",
            linha_inicio,
            coluna_inicio
        ))
        self.avancar()
        return self.proximo_token()
    
    def analisar(self) -> List[Token]:
        """Executa a análise léxica completa"""
        while True:
            token = self.proximo_token()
            if token:
                self.tokens.append(token)
                if token.tipo == TokenType.EOF:
                    break
        
        return self.tokens
    
    def imprimir_tokens(self):
        """Imprime todos os tokens encontrados"""
        print("\n=== TOKENS ENCONTRADOS ===\n")
        for token in self.tokens:
            print(token)
    
    def imprimir_erros(self):
        """Imprime todos os erros encontrados"""
        if self.erros:
            print("\n=== ERROS LÉXICOS ===\n")
            for erro in self.erros:
                print(erro)
        else:
            print("\n=== Nenhum erro léxico encontrado ===")
    
    def tem_erros(self) -> bool:
        """Verifica se há erros"""
        return len(self.erros) > 0


# Exemplo de uso
if __name__ == "__main__":
    codigo_exemplo = """
    // Programa de exemplo
    inicio
        inteiro x := 10
        flutuante y := 3.14
        cadeia nome := "João Silva"
        logico ativo := verdadeiro
        
        /* Este é um comentário
           de múltiplas linhas */
        
        para i := 1 faca
            se x > 5 senao
                escreva("Maior que 5")
            fim
        fim
        
        enquanto x >= 0 faca
            x--
        fim
        
        cadeia msg := "Olá" & " Mundo"
        y := y + 2.5
        x++
        
        leia(nome)
        escreva(nome)
    fim
    """
    
    # Criar analisador
    analisador = AnalisadorLexico(codigo_exemplo)
    
    # Executar análise
    tokens = analisador.analisar()
    
    # Imprimir resultados
    analisador.imprimir_tokens()
    analisador.imprimir_erros()
    
    print(f"\n=== RESUMO ===")
    print(f"Total de tokens: {len(tokens)}")
    print(f"Total de erros: {len(analisador.erros)}")
