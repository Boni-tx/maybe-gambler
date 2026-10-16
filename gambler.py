# -*- coding: utf-8 -*-
"""
SORTE OU MORTE
==============
Um caça-níquel "roguelike" de terror, inspirado no CloverPit
(o jogo de caça-níquel que apareceu no Xbox Partner Preview).

Você acorda preso numa cela com um caça-níquel, um caixa eletrônico e um
telefone velho. Para sair, precisa pagar a DÍVIDA antes de cada PRAZO acabar.
Se não pagar... o chão se abre.

Como jogar
----------
- Cada prazo tem 3 rodadas. No começo de cada rodada, escolha:
      MUITOS GIROS (7 giros + 1 bilhete) ou POUCOS GIROS (3 giros + 3 bilhetes).
  Os giros custam moedas.
- Símbolos iguais em linha, coluna, diagonal ou em formas especiais pagam prêmios.
- As moedas ganhas vão para o BOLSO. Deposite no CAIXA: lá elas ficam seguras
  e rendem juros no fim de cada rodada.
- Às vezes aparece o 666: o diabo leva todo o seu bolso! Depois ele liga...
- Use BILHETES para comprar AMULETOS, que mudam as regras a seu favor.
- Pague 8 dívidas para ficar livre.

Controles
---------
    Mouse ............. clique nos botões (botão direito vende amuleto)
    Espaço ............ girar (segure para girar sem parar)
    1 / 2 ............. escolher os giros da rodada
    D ................. depositar tudo no caixa
    P ................. pagar a dívida (quando der)
    T ................. atender o telefone
    R ................. trocar os amuletos da loja
    Tab ............... tabela de prêmios
    F ................. velocidade 1x / 2x
    M ................. som liga/desliga
    Esc ............... pausa
    F11 ............... tela cheia

Como rodar:   python gambler.py
Precisa de:   python -m pip install pygame-ce
"""

import array
import json
import math
import os
import random
import sys

import pygame

# =====================================================================
# CONFIGURAÇÕES
# =====================================================================
LARGURA, ALTURA = 1280, 720
FPS = 60
TITULO = "Sorte ou Morte"

if getattr(sys, "frozen", False):
    PASTA = os.path.dirname(sys.executable)
else:
    PASTA = os.path.dirname(os.path.abspath(__file__))
ARQ_RECORDE = os.path.join(PASTA, "gambler_recorde.json")

# ---------------- regras ----------------
LINHAS, COLUNAS = 3, 5
RODADAS = 3                       # rodadas em cada prazo
JUROS_BASE = 0.10                 # o caixa rende 10% no fim de cada rodada
TAXA_SAQUE = 0.10                 # sacar do caixa para pagar giros custa 10% a mais
BOLSO_INICIAL = 20
BILHETES_INICIAIS = 2
BONUS_ANTECIPADO = 3              # bilhetes por rodada que sobrar ao pagar antes
ESPACOS_AMULETO = 5
MAX_ESPACOS = 8
PRAZOS_PARA_VENCER = 8
DIVIDAS = [75, 200, 666, 1500, 4000, 10000, 25000, 66666]
CUSTO_GIRO = [1, 2, 4, 8, 15, 30, 60, 120]
PACOTES = [("MUITOS GIROS", 7, 1), ("POUCOS GIROS", 3, 3)]   # (nome, giros, bilhetes)

# ---------------- tela ----------------
CEL = 88                          # tamanho de cada casa do caça-níquel
VAO = 8                           # espaço entre as casas
PASSO = CEL + VAO
REEL_W = COLUNAS * CEL + (COLUNAS - 1) * VAO
REEL_H = LINHAS * CEL + (LINHAS - 1) * VAO
REEL_X = LARGURA // 2 - REEL_W // 2
REEL_Y = 150

# Cores
BRANCO = (255, 255, 255)
PRETO = (0, 0, 0)
CINZA = (150, 150, 160)
OURO = (255, 205, 70)
VERMELHO = (235, 55, 55)
VERDE = (90, 225, 110)
CIANO = (110, 230, 255)
LARANJA = (255, 150, 50)
ROXO = (185, 110, 245)
GIZ = (232, 232, 222)
VERDE_TELA = (90, 255, 150)

FONTES = {
    "ui": "segoeui,arial,dejavusans",
    "mono": "consolas,couriernew,dejavusansmono",
    "giz": "segoeprint,segoeui,arial",
    "titulo": "impact,arialblack,arial",
    "simbolo": "segoeuisymbol,segoeuiemoji,dejavusans",
}

# =====================================================================
# SÍMBOLOS, PADRÕES E AMULETOS
# =====================================================================
SIMBOLOS = ["limao", "cereja", "trevo", "sino", "diamante", "bau", "sete"]
INFO_SIMBOLO = {
    "limao":    {"nome": "Limão",    "plural": "Limões",    "valor": 5,  "peso": 19},
    "cereja":   {"nome": "Cereja",   "plural": "Cerejas",   "valor": 5,  "peso": 19},
    "trevo":    {"nome": "Trevo",    "plural": "Trevos",    "valor": 8,  "peso": 15},
    "sino":     {"nome": "Sino",     "plural": "Sinos",     "valor": 8,  "peso": 15},
    "diamante": {"nome": "Diamante", "plural": "Diamantes", "valor": 12, "peso": 12},
    "bau":      {"nome": "Baú",      "plural": "Baús",      "valor": 12, "peso": 12},
    "sete":     {"nome": "Sete",     "plural": "Setes",     "valor": 20, "peso": 8},
}

PADROES = {
    "trio":     {"nome": "Trio",        "mult": 1,  "desc": "3 iguais em linha",         "cor": (255, 225, 90)},
    "quadra":   {"nome": "Quadra",      "mult": 3,  "desc": "4 iguais em linha",         "cor": (255, 190, 60)},
    "quina":    {"nome": "Quina",       "mult": 6,  "desc": "5 iguais em linha",         "cor": (255, 150, 40)},
    "coluna":   {"nome": "Coluna",      "mult": 2,  "desc": "3 iguais na vertical",      "cor": (110, 230, 255)},
    "diagonal": {"nome": "Diagonal",    "mult": 2,  "desc": "3 iguais na diagonal",      "cor": (235, 130, 255)},
    "v":        {"nome": "V",           "mult": 6,  "desc": "5 iguais formando um V",    "cor": (255, 120, 90)},
    "v_inv":    {"nome": "V Invertido", "mult": 6,  "desc": "5 iguais formando um Λ",    "cor": (255, 120, 90)},
    "olho":     {"nome": "Olho",        "mult": 15, "desc": "9 iguais formando um olho", "cor": (120, 255, 150)},
    "jackpot":  {"nome": "JACKPOT",     "mult": 30, "desc": "a máquina inteira igual",   "cor": (255, 255, 255)},
}
ORDEM_PADROES = list(PADROES)

# formas fixas (as linhas horizontais são procuradas à parte)
FORMAS = []
for _c in range(COLUNAS):
    FORMAS.append(("coluna", [(0, _c), (1, _c), (2, _c)]))
for _c in range(COLUNAS - 2):
    FORMAS.append(("diagonal", [(0, _c), (1, _c + 1), (2, _c + 2)]))
    FORMAS.append(("diagonal", [(2, _c), (1, _c + 1), (0, _c + 2)]))
FORMAS.append(("v", [(0, 0), (1, 1), (2, 2), (1, 3), (0, 4)]))
FORMAS.append(("v_inv", [(2, 0), (1, 1), (0, 2), (1, 3), (2, 4)]))
FORMAS.append(("olho", [(0, 1), (0, 2), (0, 3), (1, 0), (1, 2), (1, 4), (2, 1), (2, 2), (2, 3)]))
FORMAS.append(("jackpot", [(r, c) for r in range(LINHAS) for c in range(COLUNAS)]))

# desenho de exemplo de cada padrão (para a tabela de prêmios)
EXEMPLO_PADRAO = {
    "trio": [(1, 0), (1, 1), (1, 2)],
    "quadra": [(1, 0), (1, 1), (1, 2), (1, 3)],
    "quina": [(1, c) for c in range(5)],
    "coluna": [(0, 2), (1, 2), (2, 2)],
    "diagonal": [(0, 1), (1, 2), (2, 3)],
}
for _tipo, _cel in FORMAS:
    EXEMPLO_PADRAO.setdefault(_tipo, _cel)

RARIDADES = {
    "comum":   {"nome": "Comum",   "preco": 2, "peso": 55, "cor": (165, 210, 160)},
    "incomum": {"nome": "Incomum", "preco": 4, "peso": 30, "cor": (100, 175, 255)},
    "raro":    {"nome": "Raro",    "preco": 6, "peso": 12, "cor": (255, 205, 70)},
    "maldito": {"nome": "Maldito", "preco": 3, "peso": 3,  "cor": (235, 50, 60)},
}


class Mods:
    """Todos os números que os amuletos e as ligações podem mudar."""

    def __init__(self):
        self.valor_mult = dict.fromkeys(SIMBOLOS, 1.0)
        self.peso_add = dict.fromkeys(SIMBOLOS, 0)
        self.padrao_mult = dict.fromkeys(PADROES, 1.0)
        self.mult_global = 1.0
        self.sorte = 0
        self.juros = JUROS_BASE
        self.sem_juros = False
        self.mult_666 = 1.0
        self.giros_extra = 0
        self.bilhetes_rodada = 0
        self.coringa = None
        self.equiv = {}
        self.gato = False
        self.ima = False
        self.corrente = False
        self.cranio = False
        self.terco = False
        self.desconto = 0
        self.espacos_extra = 0
        self.custo_mult = 1.0

    def valor(self, s):
        return max(1, int(round(INFO_SIMBOLO[s]["valor"] * self.valor_mult[s])))

    def peso(self, s):
        return max(1, INFO_SIMBOLO[s]["peso"] + self.peso_add[s])


# pequenas "receitas" para montar os efeitos dos amuletos
def _valor_x(s, x):
    def f(m):
        m.valor_mult[s] *= x
    return f


def _peso(s, n):
    def f(m):
        m.peso_add[s] += n
    return f


def _padrao_x(tipos, x):
    def f(m):
        for t in tipos:
            m.padrao_mult[t] *= x
    return f


def _soma(atributo, v):
    def f(m):
        setattr(m, atributo, getattr(m, atributo) + v)
    return f


def _vezes(atributo, v):
    def f(m):
        setattr(m, atributo, getattr(m, atributo) * v)
    return f


def _define(atributo, v):
    def f(m):
        setattr(m, atributo, v)
    return f


def _equiv(de, para):
    def f(m):
        m.equiv[de] = para
    return f


def _varios(*efeitos):
    def f(m):
        for e in efeitos:
            e(m)
    return f


def A(nome, desc, rar, icone, efeito):
    return {"nome": nome, "desc": desc, "rar": rar, "icone": icone, "efeito": efeito}


AMULETOS = {
    "limonada":    A("Limonada", "Limões valem o dobro.", "comum", "\U0001F34B", _valor_x("limao", 2)),
    "torta":       A("Torta de Cereja", "Cerejas valem o dobro.", "comum", "\U0001F352", _valor_x("cereja", 2)),
    "prensado":    A("Trevo Prensado", "Trevos valem o dobro.", "comum", "☘", _valor_x("trevo", 2)),
    "badalo":      A("Badalo", "Sinos valem o dobro.", "comum", "\U0001F514", _valor_x("sino", 2)),
    "joalheiro":   A("Joalheiro", "Diamantes valem o triplo.", "incomum", "\U0001F48E", _valor_x("diamante", 3)),
    "pirata":      A("Bandeira Pirata", "Baús valem o triplo.", "incomum", "☠", _valor_x("bau", 3)),
    "sete_ouro":   A("Sete de Ouro", "Setes valem 4 vezes mais.", "raro", "7", _valor_x("sete", 4)),
    "saco_limoes": A("Saco de Limões", "Muito mais Limões na máquina.", "comum", "\U0001F4B0", _peso("limao", 25)),
    "pomar":       A("Pomar", "Muito mais Cerejas na máquina.", "comum", "\U0001F333", _peso("cereja", 25)),
    "campanario":  A("Campanário", "Muito mais Sinos na máquina.", "incomum", "⛪", _peso("sino", 20)),
    "garimpo":     A("Garimpo", "Mais Diamantes na máquina.", "incomum", "⛏", _peso("diamante", 18)),
    "viciada":     A("Máquina Viciada", "Mais Setes na máquina.", "raro", "\U0001F3B0", _peso("sete", 18)),
    "dieta":       A("Dieta", "Limões e Cerejas aparecem bem menos.", "incomum", "⚖",
                     _varios(_peso("limao", -14), _peso("cereja", -14))),
    "regua":       A("Régua", "Trios, Quadras e Quinas valem o dobro.", "incomum", "\U0001F4CF",
                     _padrao_x(["trio", "quadra", "quina"], 2)),
    "prumo":       A("Prumo", "Colunas valem o triplo.", "incomum", "↕", _padrao_x(["coluna"], 3)),
    "esquadro":    A("Esquadro", "Diagonais valem o triplo.", "incomum", "\U0001F4D0", _padrao_x(["diagonal"], 3)),
    "asas":        A("Asas de Morcego", "V e V Invertido valem 5 vezes mais.", "raro", "\U0001F987",
                     _padrao_x(["v", "v_inv"], 5)),
    "olho_grego":  A("Olho Grego", "O padrão Olho vale 5 vezes mais e dá +1 de Sorte.", "raro", "\U0001F441",
                     _varios(_padrao_x(["olho"], 5), _soma("sorte", 1))),
    "trevo4":      A("Trevo de 4 Folhas", "+2 de Sorte.", "incomum", "\U0001F340", _soma("sorte", 2)),
    "coelho":      A("Pé de Coelho", "+5 de Sorte.", "raro", "\U0001F407", _soma("sorte", 5)),
    "ferradura":   A("Ferradura", "+1 de Sorte e o 666 aparece 40% menos.", "incomum", "Ω",
                     _varios(_soma("sorte", 1), _vezes("mult_666", 0.6))),
    "cofrinho":    A("Cofrinho", "O caixa rende +5% de juros.", "comum", "\U0001F437", _soma("juros", 0.05)),
    "bilhete":     A("Bilhete Dourado", "+1 bilhete em toda rodada.", "incomum", "\U0001F3AB", _soma("bilhetes_rodada", 1)),
    "gato":        A("Gato Preto", "Giro sem prêmio paga um consolo (3 giros de volta).", "comum", "\U0001F408",
                     _define("gato", True)),
    "calculadora": A("Calculadora", "Todos os prêmios valem o dobro.", "raro", "✖", _vezes("mult_global", 2)),
    "dado":        A("Dado Extra", "+1 giro em toda rodada.", "incomum", "⚄", _soma("giros_extra", 1)),
    "cupom":       A("Cupom", "Amuletos custam 1 bilhete a menos.", "comum", "✂", _soma("desconto", 1)),
    "corrente":    A("Corrente da Sorte", "Cada padrão no mesmo giro vale 50% a mais que o anterior.", "raro", "⛓",
                     _define("corrente", True)),
    "ima":         A("Caça-Bilhetes", "Giro com 3 ou mais padrões dá 1 bilhete.", "incomum", "\U0001F39F",
                     _define("ima", True)),
    "coringa":     A("Coringa", "Trevos viram curinga: combinam com qualquer símbolo.", "raro", "\U0001F0CF",
                     _define("coringa", "trevo")),
    "fruteira":    A("Fruteira", "Limões e Cerejas contam como o mesmo símbolo.", "incomum", "\U0001F347",
                     _equiv("cereja", "limao")),
    "terco":       A("Terço", "Se sair 666, você perde só metade do bolso.", "comum", "✝", _define("terco", True)),
    "contrato":    A("Contrato Sangrento", "Prêmios valem o triplo, mas o caixa não rende mais juros.", "maldito",
                     "\U0001F4DC", _varios(_vezes("mult_global", 3), _define("sem_juros", True))),
    "chifre":      A("Chifre do Diabo", "Prêmios valem 4 vezes mais, mas o 666 aparece o dobro.", "maldito",
                     "\U0001F608", _varios(_vezes("mult_global", 4), _vezes("mult_666", 2))),
    "cranio":      A("Crânio Sorridente", "Quando sair 666, você GANHA moedas em vez de perder.", "maldito",
                     "\U0001F480", _define("cranio", True)),
    "vela":        A("Vela Preta", "+6 de Sorte, mas toda rodada tem 1 giro a menos.", "maldito", "\U0001F56F",
                     _varios(_soma("sorte", 6), _soma("giros_extra", -1))),
}


def _etiquetas(aid):
    """Descobre o que um amuleto mexe (para fazê-lo pular quando ajudar num prêmio)."""
    m0, m1 = Mods(), Mods()
    AMULETOS[aid]["efeito"](m1)
    tags = set()
    for s in SIMBOLOS:
        if m1.valor_mult[s] != m0.valor_mult[s]:
            tags.add("valor:" + s)
    for t in PADROES:
        if m1.padrao_mult[t] != m0.padrao_mult[t]:
            tags.add("padrao:" + t)
    if m1.mult_global != m0.mult_global:
        tags.add("global")
    if m1.corrente:
        tags.add("corrente")
    if m1.coringa:
        tags.add("coringa")
    if m1.equiv:
        tags.add("equiv")
    return tags


for _aid in AMULETOS:
    AMULETOS[_aid]["tags"] = _etiquetas(_aid)


# =====================================================================
# REGRAS DO JOGO (sem nada de desenho)
# =====================================================================
def divida_base(prazo):
    if prazo <= len(DIVIDAS):
        return DIVIDAS[prazo - 1]
    return int(DIVIDAS[-1] * 2.5 ** (prazo - len(DIVIDAS)))     # modo infinito


def custo_giro(prazo):
    if prazo <= len(CUSTO_GIRO):
        return CUSTO_GIRO[prazo - 1]
    return int(CUSTO_GIRO[-1] * 2 ** (prazo - len(CUSTO_GIRO)))


def chance_666_base(prazo):
    return min(0.12, 0.015 + 0.004 * (prazo - 1))


class Padrao:
    __slots__ = ("tipo", "celulas", "simbolo")

    def __init__(self, tipo, celulas):
        self.tipo, self.celulas, self.simbolo = tipo, celulas, None


def representante(simbolos, coringa, equiv):
    """Se todos os símbolos combinam, devolve qual símbolo eles formam. Senão, None."""
    base = None
    for s in simbolos:
        if s == coringa:
            continue
        k = equiv.get(s, s)
        if base is None:
            base = k
        elif k != base:
            return None
    return base if base is not None else coringa


def encontrar_padroes(grade, coringa=None, equiv=None):
    equiv = equiv or {}
    achados = []
    for r in range(LINHAS):                      # linhas: pega a sequência mais longa
        linha = grade[r]
        c = 0
        while c <= COLUNAS - 3:
            tam = 0
            for fim in range(COLUNAS, c + 2, -1):
                if representante(linha[c:fim], coringa, equiv) is not None:
                    tam = fim - c
                    break
            if tam:
                tipo = {3: "trio", 4: "quadra", 5: "quina"}[tam]
                achados.append(Padrao(tipo, [(r, k) for k in range(c, c + tam)]))
                c += tam
            else:
                c += 1
    for tipo, cel in FORMAS:
        if representante([grade[r][c] for r, c in cel], coringa, equiv) is not None:
            achados.append(Padrao(tipo, cel))
    return achados


class Giro:
    def __init__(self, grade):
        self.grade = grade
        self.padroes = []
        self.premios = []
        self.total = 0
        self.diabo = False
        self.perda = 0
        self.ganho_diabo = 0
        self.consolo = 0
        self.bilhetes = 0


def aplicar_bencao(m, b):
    """Ofertas do telefone que ficam valendo para sempre."""
    t = b["tipo"]
    if t == "sorte":
        m.sorte += b["n"]
    elif t == "juros":
        m.juros += b["v"]
    elif t == "giros":
        m.giros_extra += b["n"]
    elif t == "valor":
        m.valor_mult[b["s"]] *= 2
    elif t == "padrao":
        for p in b["ps"]:
            m.padrao_mult[p] *= 2
    elif t == "peso":
        m.peso_add[b["s"]] += 12
    elif t == "espaco":
        m.espacos_extra += 1
    elif t == "anti666":
        m.mult_666 *= 0.5
    elif t == "pacto_premio":
        m.mult_global *= 2
        m.mult_666 *= 2
    elif t == "pacto_sorte":
        m.sorte += 6
        m.giros_extra -= 1
    elif t == "pacto_juros":
        m.juros += 0.15
        m.custo_mult *= 2


class Partida:
    def __init__(self, semente=None):
        self.rng = random.Random(semente)
        self.prazo = 1
        self.rodada = 1
        self.rodada_iniciada = False
        self.giros = 0
        self.bolso = BOLSO_INICIAL
        self.caixa = 0
        self.bilhetes = BILHETES_INICIAIS
        self.amuletos = []
        self.bencaos = []
        self.divida_extra = 0.0
        self.custo_troca = 1
        self.maldicao = False
        self.venceu = False
        self.prazos_pagos = 0
        self.ajuda_banco = 0
        self.loja = []
        self.stats = {"giros": 0, "ganho": 0, "maior_giro": 0, "diabos": 0, "padroes": 0,
                      "jackpots": 0, "comprados": 0}
        self.recalcular()
        self.nova_loja()

    # ---------- números derivados ----------
    def recalcular(self):
        m = Mods()
        for b in self.bencaos:
            aplicar_bencao(m, b)
        for a in self.amuletos:
            AMULETOS[a]["efeito"](m)
        self.mods = m

    @property
    def divida(self):
        return int(divida_base(self.prazo) * (1 + self.divida_extra))

    @property
    def espacos(self):
        return min(MAX_ESPACOS, ESPACOS_AMULETO + self.mods.espacos_extra)

    def custo_do_giro(self):
        return custo_giro(self.prazo) * self.mods.custo_mult

    def chance_666(self):
        return min(0.5, chance_666_base(self.prazo) * self.mods.mult_666)

    def juros_atual(self):
        return 0.0 if self.mods.sem_juros else self.mods.juros

    # ---------- rodada ----------
    def opcoes_pacote(self):
        c = self.custo_do_giro()
        ops = []
        for nome, giros, bilhetes in PACOTES:
            g = max(1, giros + self.mods.giros_extra)
            custo = int(math.ceil(g * c))
            falta = max(0, custo - self.bolso)
            saque = int(math.ceil(falta * (1 + TAXA_SAQUE)))
            ops.append({"nome": nome, "giros": g, "bilhetes": bilhetes + self.mods.bilhetes_rodada,
                        "custo": custo, "saque": saque, "pode": saque <= self.caixa})
        return ops

    def comprar_pacote(self, i):
        op = self.opcoes_pacote()[i]
        if not op["pode"]:
            return None
        if op["saque"]:
            self.caixa -= op["saque"]
            self.bolso = 0
        else:
            self.bolso -= op["custo"]
        self.giros = op["giros"]
        self.bilhetes += op["bilhetes"]
        self.rodada_iniciada = True
        return op

    def passar_rodada(self):
        self.rodada_iniciada = True
        self.giros = 0

    # ---------- giro ----------
    def gerar_grade(self):
        m = self.mods
        rng = self.rng
        pesos = [m.peso(s) for s in SIMBOLOS]
        p_sorte = min(0.5, m.sorte * 0.03)       # Sorte: a casa copia um vizinho
        grade = [[None] * COLUNAS for _ in range(LINHAS)]
        for r in range(LINHAS):
            for c in range(COLUNAS):
                s = rng.choices(SIMBOLOS, pesos)[0]
                if p_sorte > 0 and rng.random() < p_sorte:
                    viz = [(a, b) for a, b in ((r, c - 1), (r - 1, c - 1), (r - 1, c), (r - 1, c + 1))
                           if a >= 0 and 0 <= b < COLUNAS and grade[a][b] is not None]
                    if viz:
                        a, b = rng.choice(viz)
                        s = grade[a][b]
                grade[r][c] = s
        return grade

    def sortear_giro(self):
        """Sorteia o resultado (gasta 1 giro). O dinheiro só muda em aplicar_giro."""
        if self.giros <= 0:
            return None
        self.giros -= 1
        m = self.mods
        g = Giro(self.gerar_grade())
        if self.rng.random() < self.chance_666():
            g.diabo = True
            for c in (1, 2, 3):
                g.grade[1][c] = "seis"
            if m.cranio:
                g.ganho_diabo = 66 * custo_giro(self.prazo)
            else:
                g.perda = self.bolso // 2 if m.terco else self.bolso
            return g
        g.padroes = encontrar_padroes(g.grade, m.coringa, m.equiv)
        g.padroes.sort(key=lambda p: (ORDEM_PADROES.index(p.tipo), p.celulas[0]))
        combo = 1.0
        for p in g.padroes:
            simbs = [g.grade[r][c] for r, c in p.celulas]
            reais = [s for s in simbs if s != m.coringa] or [m.coringa]
            p.simbolo = max(reais, key=m.valor)
            v = m.valor(p.simbolo) * PADROES[p.tipo]["mult"] * m.padrao_mult[p.tipo] * m.mult_global * combo
            if m.corrente:
                combo += 0.5
            g.premios.append(max(1, int(round(v))))
        g.total = sum(g.premios)
        if not g.padroes and m.gato:
            g.consolo = 3 * custo_giro(self.prazo)
        if m.ima and len(g.padroes) >= 3:
            g.bilhetes = 1
        return g

    def aplicar_giro(self, g):
        st = self.stats
        st["giros"] += 1
        if g.diabo:
            self.bolso = self.bolso - g.perda + g.ganho_diabo
            self.maldicao = True
            st["diabos"] += 1
        else:
            ganho = g.total + g.consolo
            self.bolso += ganho
            self.bilhetes += g.bilhetes
            st["ganho"] += ganho
            st["maior_giro"] = max(st["maior_giro"], g.total)
            st["padroes"] += len(g.padroes)
            if any(p.tipo == "jackpot" for p in g.padroes):
                st["jackpots"] += 1

    # ---------- caixa ----------
    def depositar(self, qtd=None):
        qtd = self.bolso if qtd is None else max(0, min(qtd, self.bolso))
        self.bolso -= qtd
        self.caixa += qtd
        return qtd

    def fim_rodada(self):
        j = int(self.caixa * self.juros_atual())
        self.caixa += j
        self.rodada_iniciada = False
        self.giros = 0
        return j

    def checar_prazo(self):
        """Fim da 3ª rodada: paga se der. True = sobreviveu."""
        self.caixa += self.bolso
        self.bolso = 0
        if self.caixa >= self.divida:
            self.caixa -= self.divida
            self.prazos_pagos += 1
            return True
        return False

    def pode_pagar_agora(self):
        return self.caixa >= self.divida

    def pagar_agora(self):
        puladas = RODADAS - self.rodada + (0 if self.rodada_iniciada else 1)
        bonus = BONUS_ANTECIPADO * max(0, puladas)
        self.caixa -= self.divida
        self.bilhetes += bonus
        self.giros = 0
        self.prazos_pagos += 1
        return bonus

    def concluir_prazo(self):
        """Avança para o próximo prazo. Devolve (ofertas do telefone, se a ligação é maldita)."""
        self.prazo += 1
        self.rodada = 1
        self.rodada_iniciada = False
        self.giros = 0
        self.divida_extra = 0.0
        self.custo_troca = 1
        # o banco "empresta" o suficiente para uma rodada, para ninguém ficar sem poder girar
        self.ajuda_banco = PACOTES[0][1] * custo_giro(self.prazo)
        self.bolso += self.ajuda_banco
        maldita = self.maldicao
        self.maldicao = False
        self.nova_loja()
        return gerar_ligacao(self, maldita), maldita

    # ---------- loja ----------
    def nova_loja(self):
        disp = [a for a in AMULETOS if a not in self.amuletos]
        self.loja = []
        for _ in range(3):
            cands = [a for a in disp if a not in self.loja]
            if not cands:
                break
            pesos = [RARIDADES[AMULETOS[a]["rar"]]["peso"] for a in cands]
            self.loja.append(self.rng.choices(cands, pesos)[0])

    def preco(self, a):
        return max(1, RARIDADES[AMULETOS[a]["rar"]]["preco"] - self.mods.desconto)

    def valor_venda(self, a):
        return max(1, RARIDADES[AMULETOS[a]["rar"]]["preco"] // 2)

    def comprar(self, i):
        a = self.loja[i] if 0 <= i < len(self.loja) else None
        if a is None or self.bilhetes < self.preco(a) or len(self.amuletos) >= self.espacos:
            return False
        self.bilhetes -= self.preco(a)
        self.amuletos.append(a)
        self.loja[i] = None
        self.stats["comprados"] += 1
        self.recalcular()
        return True

    def vender(self, idx):
        if not 0 <= idx < len(self.amuletos):
            return 0
        a = self.amuletos.pop(idx)
        v = self.valor_venda(a)
        self.bilhetes += v
        self.recalcular()
        return v

    def trocar_loja(self):
        if self.bilhetes < self.custo_troca:
            return False
        self.bilhetes -= self.custo_troca
        self.custo_troca += 1
        self.nova_loja()
        return True


# ---------------- telefone ----------------
def gerar_ligacao(p, maldita):
    rng = p.rng
    if maldita:
        tipos = ["pacto_premio", "pacto_ouro", "pacto_amuleto", "pacto_sorte", "pacto_juros"]
    else:
        tipos = ["sorte", "juros", "giros", "bilhetes", "valor", "padrao", "peso", "espaco", "amuleto", "anti666"]
    rng.shuffle(tipos)
    ofertas = []
    for t in tipos:
        o = {"tipo": t}
        if t in ("valor", "peso"):
            o["s"] = rng.choice(SIMBOLOS)
        elif t == "padrao":
            o["ps"] = rng.choice([["trio", "quadra", "quina"], ["coluna"], ["diagonal"], ["v", "v_inv"]])
        elif t == "bilhetes":
            o["n"] = 3 + p.prazo // 2
        elif t == "sorte":
            o["n"] = 2
        elif t == "giros":
            o["n"] = 1
        elif t == "juros":
            o["v"] = 0.05
        elif t == "espaco" and p.espacos >= MAX_ESPACOS:
            continue
        elif t in ("amuleto", "pacto_amuleto"):
            rars = ["maldito"] if t == "pacto_amuleto" else ["incomum", "raro"]
            cands = [a for a in AMULETOS if AMULETOS[a]["rar"] in rars and a not in p.amuletos]
            if not cands:
                continue
            o["id"] = rng.choice(cands)
        elif t == "pacto_ouro":
            o["n"] = int(p.divida * 0.4)
        ofertas.append(o)
        if len(ofertas) == 3:
            break
    return ofertas


def oferta_valida(p, o):
    if o["tipo"] in ("amuleto", "pacto_amuleto"):
        return len(p.amuletos) < p.espacos and o["id"] not in p.amuletos
    return True


def aplicar_oferta(p, o):
    t = o["tipo"]
    if t == "bilhetes":
        p.bilhetes += o["n"]
    elif t in ("amuleto", "pacto_amuleto"):
        if oferta_valida(p, o):
            p.amuletos.append(o["id"])
    elif t == "pacto_ouro":
        p.bolso += o["n"]
        p.divida_extra += 0.5
    else:
        p.bencaos.append(o)
    p.recalcular()


def texto_oferta(p, o):
    """(título, descrição, ícone) de uma oferta do telefone."""
    t = o["tipo"]
    nome_ps = {"trio": "Linhas", "coluna": "Colunas", "diagonal": "Diagonais", "v": "Vs"}
    if t == "sorte":
        return f"+{o['n']} de Sorte", "Os símbolos se repetem mais. Para sempre.", "\U0001F340"
    if t == "juros":
        return "+5% de Juros", "O caixa rende mais no fim de cada rodada.", "\U0001F437"
    if t == "giros":
        return "+1 Giro", "Toda rodada terá 1 giro a mais. Para sempre.", "⚄"
    if t == "bilhetes":
        return f"{o['n']} Bilhetes", "Bilhetes para gastar na loja de amuletos.", "\U0001F3AB"
    if t == "valor":
        pl = INFO_SIMBOLO[o["s"]]["plural"]
        return f"{pl} em dobro", f"{pl} valem o dobro. Para sempre.", "simbolo:" + o["s"]
    if t == "padrao":
        nome = nome_ps[o["ps"][0]]
        extra = " (Trio, Quadra e Quina)" if o["ps"][0] == "trio" else ""
        return f"{nome} em dobro", f"{nome}{extra} pagam o dobro. Para sempre.", "\U0001F4CF"
    if t == "peso":
        pl = INFO_SIMBOLO[o["s"]]["plural"]
        return f"Mais {pl}", f"{pl} aparecem bem mais na máquina.", "simbolo:" + o["s"]
    if t == "espaco":
        return "+1 Espaço", "Carregue um amuleto a mais.", "➕"
    if t == "amuleto":
        a = AMULETOS[o["id"]]
        return f"Ganhe: {a['nome']}", a["desc"], "amuleto:" + o["id"]
    if t == "anti666":
        return "Proteção", "O 666 aparece pela metade. Para sempre.", "✝"
    if t == "pacto_premio":
        return "Pacto da Ganância", "Todos os prêmios valem o dobro para sempre... mas o 666 aparece o DOBRO.", "\U0001F608"
    if t == "pacto_ouro":
        return f"{formatar(o['n'])} moedas", "Moedas agora mesmo... mas a dívida deste prazo sobe 50%.", "\U0001F4B0"
    if t == "pacto_amuleto":
        a = AMULETOS[o["id"]]
        return f"Ganhe: {a['nome']}", a["desc"] + " (amuleto MALDITO, de graça)", "amuleto:" + o["id"]
    if t == "pacto_sorte":
        return "Pacto da Sorte", "+6 de Sorte para sempre... mas toda rodada tem 1 giro a menos.", "\U0001F56F"
    if t == "pacto_juros":
        return "Pacto do Agiota", "+15% de juros para sempre... mas os giros custam o DOBRO.", "\U0001F4DC"
    return t, "", "?"


# =====================================================================
# FUNÇÕES AUXILIARES
# =====================================================================
def limitar(v, a, b):
    return a if v < a else b if v > b else v


def escurecer(cor, f):
    return (int(cor[0] * f), int(cor[1] * f), int(cor[2] * f))


def clarear(cor, f):
    return (int(cor[0] + (255 - cor[0]) * f), int(cor[1] + (255 - cor[1]) * f), int(cor[2] + (255 - cor[2]) * f))


def misturar(a, b, t):
    return (int(a[0] + (b[0] - a[0]) * t), int(a[1] + (b[1] - a[1]) * t), int(a[2] + (b[2] - a[2]) * t))


def formatar(n):
    """12345 -> '12.345' (e números enormes viram '1,2 mi')."""
    n = int(n)
    if abs(n) >= 1_000_000_000:
        return f"{n / 1e9:.1f} bi".replace(".", ",")
    if abs(n) >= 1_000_000:
        return f"{n / 1e6:.1f} mi".replace(".", ",")
    return f"{n:,}".replace(",", ".")


def porcento(v):
    x = v * 100
    if abs(x - round(x)) < 0.05:
        return f"{int(round(x))}%"
    return f"{x:.1f}%".replace(".", ",")


def vezes(x):
    if abs(x - round(x)) < 0.01:
        return f"×{int(round(x))}"
    return f"×{x:.1f}".replace(".", ",")


def suave(t):
    t = limitar(t, 0.0, 1.0)
    return t * t * (3 - 2 * t)


def _bezier(a, b, c, n=14):
    pts = []
    for i in range(n + 1):
        t = i / n
        pts.append(((1 - t) ** 2 * a[0] + 2 * (1 - t) * t * b[0] + t * t * c[0],
                    (1 - t) ** 2 * a[1] + 2 * (1 - t) * t * b[1] + t * t * c[1]))
    return pts


def _quantizar(r):
    r = int(r)
    if r <= 16:
        return max(2, r)
    if r <= 64:
        return r // 4 * 4
    return min(300, r // 16 * 16)


_cache_brilho = {}


def brilho(cor, raio):
    """Círculo com degradê para usar com BLEND_ADD (efeito de luz)."""
    raio = _quantizar(raio)
    chave = (tuple(cor), raio)
    sup = _cache_brilho.get(chave)
    if sup is None:
        sup = pygame.Surface((raio * 2, raio * 2))
        for r in range(raio, 0, -1):
            k = (1 - r / raio) ** 1.7
            pygame.draw.circle(sup, (int(cor[0] * k), int(cor[1] * k), int(cor[2] * k)), (raio, raio), r)
        if len(_cache_brilho) > 300:
            _cache_brilho.clear()
        _cache_brilho[chave] = sup
    return sup


def carregar_recorde():
    base = {"melhor_prazo": 0, "maior_giro": 0, "vitorias": 0, "partidas": 0}
    try:
        with open(ARQ_RECORDE, encoding="utf-8") as arq:
            dados = json.load(arq)
        for k in base:
            base[k] = int(dados.get(k, 0))
    except Exception:
        pass
    return base


def salvar_recorde(dados):
    try:
        with open(ARQ_RECORDE, "w", encoding="utf-8") as arq:
            json.dump(dados, arq)
    except Exception:
        pass


# =====================================================================
# SONS (gerados pelo próprio código)
# =====================================================================
class Sons:
    def __init__(self):
        self.ok = False
        self.mudo = False
        self.sons = {}
        self.ultimo = {}
        self.canal_ambiente = None
        try:
            if not pygame.mixer.get_init():
                pygame.mixer.init(22050, -16, 2, 512)
            self.taxa, _, self.canais = pygame.mixer.get_init()
            pygame.mixer.set_num_channels(32)
            self._criar()
            self.ok = True
        except Exception as erro:
            print("Aviso: som desativado ->", erro)

    def _som(self, dur, gerar, volume=0.5):
        n = max(1, int(self.taxa * dur))
        mono = array.array("h", bytes(2 * n))
        for i in range(n):
            v = gerar(i / self.taxa, i / n) * volume
            mono[i] = int(32000 * (1.0 if v > 1 else -1.0 if v < -1 else v))
        if self.canais == 1:
            dados = mono
        else:
            dados = array.array("h", bytes(2 * n * self.canais))
            for c in range(self.canais):
                dados[c::self.canais] = mono
        return pygame.mixer.Sound(buffer=dados.tobytes())

    def _osc(self, forma, f0, f1=None, curva=1.0):
        taxa = self.taxa
        if f1 is None:
            f1 = f0
        fase = [0.0]

        def g(p):
            f = f0 + (f1 - f0) * (p ** curva)
            fase[0] = (fase[0] + f / taxa) % 1.0
            x = fase[0]
            if forma == "seno":
                return math.sin(math.tau * x)
            if forma == "quadrada":
                return 1.0 if x < 0.5 else -1.0
            if forma == "serra":
                return 2 * x - 1
            return 1 - 4 * abs(x - 0.5)
        return g

    def _ruido(self, suave_=1.0):
        estado = [0.0]

        def g(s=None):
            k = suave_ if s is None else s
            estado[0] += (random.uniform(-1, 1) - estado[0]) * k
            return estado[0]
        return g

    def _arpejo(self, notas, forma, dur_nota=None):
        oscs = [self._osc(forma, f) for f in notas]
        n = len(notas)

        def g(t, p):
            i = min(n - 1, int(p * n))
            local = p * n - i
            return oscs[i](p) * (1 - local) ** 0.6 * (1 - p * 0.4)
        return g

    def _criar(self):
        S = self.sons
        r = self._ruido(0.5)
        o = self._osc("seno", 150, 55)
        S["alavanca"] = self._som(0.28, lambda t, p: r() * 0.7 * (1 - p) ** 8 + o(p) * 0.9 * (1 - p) ** 2, 0.5)

        r = self._ruido(0.9)
        S["tick"] = self._som(0.03, lambda t, p: r() * (1 - p) ** 2, 0.18)

        for i in range(COLUNAS):
            o = self._osc("seno", 190 - i * 14, 70)
            rr = self._ruido(0.35)
            S[f"para{i}"] = self._som(0.16, lambda t, p, o=o, rr=rr: (o(p) * 0.9 + rr() * 0.5) * (1 - p) ** 3, 0.5)

        notas = [523, 587, 659, 698, 784, 880, 988, 1047, 1175, 1319, 1397, 1568]
        for i, f in enumerate(notas):
            o1 = self._osc("seno", f)
            o2 = self._osc("seno", f * 2.01)
            o3 = self._osc("triangulo", f * 3)
            S[f"ding{i}"] = self._som(0.38, lambda t, p, o1=o1, o2=o2, o3=o3:
                                      (o1(p) * 0.7 + o2(p) * 0.25 + o3(p) * 0.08) * (1 - p) ** 2.2 * min(1.0, p * 80), 0.35)

        o1 = self._osc("seno", 2093)
        o2 = self._osc("seno", 3136)
        S["moeda"] = self._som(0.16, lambda t, p: (o1(p) * 0.5 + (o2(p) * 0.45 if p > 0.25 else 0)) * (1 - p) ** 2, 0.25)

        o1 = self._osc("quadrada", 880)
        o2 = self._osc("quadrada", 1320)
        S["deposito"] = self._som(0.22, lambda t, p: (o1(p) if p < 0.4 else (o2(p) if p > 0.55 else 0)) * (1 - p * 0.5), 0.14)

        S["juros"] = self._som(0.55, self._arpejo([659, 988, 1319], "seno"), 0.3)

        o = self._osc("seno", 1568)
        r = self._ruido(0.7)
        S["compra"] = self._som(0.45, lambda t, p: o(p) * (1 - p) ** 1.5 * 0.7 + (r() * (1 - p / 0.15) * 0.6 if p < 0.15 else 0), 0.35)

        o = self._osc("quadrada", 110, 90)
        S["erro"] = self._som(0.22, lambda t, p: o(p) * (1 - p), 0.22)

        o = self._osc("seno", 1200, 400)
        S["virar"] = self._som(0.05, lambda t, p: o(p) * (1 - p) ** 2, 0.2)

        o1 = self._osc("seno", 440)
        o2 = self._osc("seno", 480)
        S["telefone"] = self._som(1.15, lambda t, p: (o1(p) + o2(p)) * 0.5 * (0.5 + 0.5 * math.sin(t * math.tau * 20))
                                  * (1.0 if p < 0.85 else (1 - p) / 0.15), 0.3)

        r = self._ruido(0.8)
        S["atender"] = self._som(0.12, lambda t, p: r() * (1 - p) ** 3, 0.4)

        o = self._osc("serra", 125, 70)
        o2 = self._osc("seno", 55, 40)
        r = self._ruido(0.15)

        def risada(t, p):
            fase = (p * 5) % 1.0
            env = math.sin(math.pi * fase / 0.7) if fase < 0.7 else 0.0
            return (o(p) * 0.7 + r() * 0.6) * env * (1 - p * 0.4) + o2(p) * 0.6 * (1 - p)
        S["diabo"] = self._som(1.8, risada, 0.55)

        o = self._osc("serra", 320, 70)
        o3 = self._osc("seno", 60, 28)
        r = self._ruido(0.1)

        def queda(t, p):
            if p < 0.22:
                q = p / 0.22
                return o(q) * 0.45 * (1 - q) * (0.7 + 0.3 * math.sin(t * 90)) + r(0.5) * 0.15
            if p < 0.88:
                q = (p - 0.22) / 0.66
                return r(0.03 + 0.25 * q) * 2.2 * math.sin(math.pi * q)
            q = (p - 0.88) / 0.12
            return o3(q) * (1 - q) ** 2 + r(0.4) * 0.4 * (1 - q) ** 3
        S["queda"] = self._som(2.6, queda, 0.6)

        S["pagar"] = self._som(0.8, self._arpejo([523, 659, 784, 1047, 1319], "quadrada"), 0.18)
        S["vitoria"] = self._som(1.8, self._arpejo([392, 523, 659, 784, 1047, 784, 1047, 1319], "quadrada"), 0.18)
        S["grande"] = self._som(0.9, self._arpejo([784, 988, 1175, 1568, 1976], "seno"), 0.35)

        o1 = self._osc("quadrada", 523)
        o2 = self._osc("quadrada", 659)
        o3 = self._osc("quadrada", 784)
        S["jackpot"] = self._som(1.6, lambda t, p: (o1(p) + o2(p) + o3(p)) / 3 * (0.6 + 0.4 * math.sin(t * math.tau * 8))
                                 * (1 - p) ** 0.7, 0.25)

        o = self._osc("seno", 300, 900)
        S["suspense"] = self._som(0.7, lambda t, p: o(p) * 0.6 * (0.5 + 0.5 * math.sin(t * math.tau * 14)) * min(1, p * 4), 0.25)

        o1 = self._osc("seno", 120)
        o2 = self._osc("seno", 240)
        o3 = self._osc("quadrada", 120)
        S["zumbido"] = self._som(2.0, lambda t, p: (o1(p) * 0.5 + o2(p) * 0.25 + o3(p) * 0.04)
                                 * (0.8 + 0.2 * math.sin(t * math.pi)), 0.10)

    def tocar(self, nome, volume=1.0, intervalo=0.0):
        if not self.ok or self.mudo:
            return
        agora = pygame.time.get_ticks()
        if intervalo and agora - self.ultimo.get(nome, -99999) < intervalo * 1000:
            return
        self.ultimo[nome] = agora
        som = self.sons.get(nome)
        if som is not None:
            canal = som.play()
            if canal:
                canal.set_volume(volume)

    def ambiente(self, ligar):
        if not self.ok:
            return
        if ligar and not self.mudo:
            if self.canal_ambiente is None or not self.canal_ambiente.get_busy():
                self.canal_ambiente = self.sons["zumbido"].play(loops=-1)
        elif self.canal_ambiente is not None:
            self.canal_ambiente.stop()
            self.canal_ambiente = None


# =====================================================================
# NITIDEZ NO WINDOWS
# =====================================================================
def ativar_nitidez():
    """Avisa o Windows que o jogo cuida da própria escala.

    Sem isso, com a escala do Windows em 125% ou 150%, a janela é "esticada"
    pelo sistema e tudo fica borrado e serrilhado.
    """
    if sys.platform != "win32":
        return
    os.environ.setdefault("SDL_WINDOWS_DPI_AWARENESS", "permonitorv2")
    try:
        import ctypes
        try:
            ctypes.windll.shcore.SetProcessDpiAwareness(2)
        except Exception:
            ctypes.windll.user32.SetProcessDPIAware()
    except Exception:
        pass


# =====================================================================
# DESENHOS (tudo feito por código, sem imagens)
#
# As posições do jogo são pensadas numa tela de 1280x720 ("coordenadas
# lógicas"), mas tudo é desenhado na resolução real da janela (fator k).
# As formas são desenhadas maiores e depois reduzidas: isso suaviza as bordas.
# =====================================================================
def _sup(S):
    return pygame.Surface((S, S), pygame.SRCALPHA)


def _simbolo_limao(S):
    u = S / 176
    s = _sup(S)
    corpo = _sup(S)
    am, esc, cla = (250, 212, 45), (185, 135, 15), (255, 246, 170)
    r = pygame.Rect(0, 0, int(S * 0.64), int(S * 0.46))
    r.center = (S // 2, S // 2)
    pygame.draw.ellipse(corpo, esc, r.inflate(round(10 * u), round(10 * u)))
    for sx in (-1, 1):
        pygame.draw.circle(corpo, esc, (S // 2 + sx * int(S * 0.33), S // 2), int(S * 0.075))
    pygame.draw.ellipse(corpo, am, r)
    for sx in (-1, 1):
        pygame.draw.circle(corpo, am, (S // 2 + sx * int(S * 0.32), S // 2), int(S * 0.05))
    b = pygame.Rect(0, 0, int(S * 0.26), int(S * 0.10))
    b.center = (int(S * 0.42), int(S * 0.41))
    pygame.draw.ellipse(corpo, cla, b)
    rnd = random.Random(4)
    for _ in range(16):
        pygame.draw.circle(corpo, (230, 188, 30), (rnd.randint(int(S * 0.3), int(S * 0.72)), rnd.randint(int(S * 0.46), int(S * 0.66))),
                           max(1, round(2 * u)))
    corpo = pygame.transform.rotozoom(corpo, 20, 1.0)
    s.blit(corpo, corpo.get_rect(center=(S // 2, int(S * 0.56))))
    folha = _sup(S)
    f = pygame.Rect(0, 0, int(S * 0.32), int(S * 0.13))
    f.center = (S // 2, S // 2)
    pygame.draw.ellipse(folha, (30, 100, 35), f.inflate(round(8 * u), round(8 * u)))
    pygame.draw.ellipse(folha, (85, 185, 70), f)
    pygame.draw.line(folha, (40, 120, 40), (f.left + 8 * u, f.centery), (f.right - 8 * u, f.centery), max(1, round(3 * u)))
    folha = pygame.transform.rotozoom(folha, 30, 1.0)
    s.blit(folha, folha.get_rect(center=(int(S * 0.64), int(S * 0.24))))
    return s


def _simbolo_cereja(S):
    u = S / 176
    s = _sup(S)
    topo = (S * 0.58, S * 0.13)
    c1, c2 = (S * 0.32, S * 0.68), (S * 0.67, S * 0.71)
    r = S * 0.17
    for c in (c1, c2):
        meio = ((topo[0] + c[0]) / 2 - S * 0.06, S * 0.34)
        pts = _bezier(topo, meio, (c[0], c[1] - r * 0.8))
        pygame.draw.lines(s, (70, 45, 20), False, pts, max(1, round(8 * u)))
        pygame.draw.lines(s, (115, 150, 55), False, pts, max(1, round(3 * u)))
    folha = [(S * 0.58, S * 0.14), (S * 0.72, S * 0.05), (S * 0.88, S * 0.10), (S * 0.74, S * 0.20)]
    pygame.draw.polygon(s, (75, 165, 60), folha)
    pygame.draw.polygon(s, (30, 90, 30), folha, max(1, round(3 * u)))
    for c in (c1, c2):
        pygame.draw.circle(s, (105, 8, 22), c, r + 5 * u)
        pygame.draw.circle(s, (212, 28, 48), c, r)
        pygame.draw.circle(s, (236, 80, 92), (c[0] - r * 0.25, c[1] - r * 0.25), r * 0.45)
        pygame.draw.circle(s, (212, 28, 48), (c[0] - r * 0.08, c[1] - r * 0.08), r * 0.42)
        pygame.draw.circle(s, (255, 225, 230), (c[0] - r * 0.42, c[1] - r * 0.42), r * 0.14)
    return s


def _simbolo_trevo(S):
    u = S / 176
    s = _sup(S)
    cx, cy = S * 0.5, S * 0.44
    escuro, verde, claro = (20, 88, 35), (60, 172, 72), (150, 230, 140)
    caule = _bezier((cx, cy), (cx + S * 0.04, cy + S * 0.26), (cx + S * 0.18, S * 0.9))
    pygame.draw.lines(s, escuro, False, caule, max(1, round(11 * u)))
    pygame.draw.lines(s, (75, 155, 60), False, caule, max(1, round(4 * u)))
    folhas = []
    for ang in (-90, 0, 90, 180):
        a = math.radians(ang)
        d = S * 0.17
        fx, fy = cx + math.cos(a) * d, cy + math.sin(a) * d
        px, py = -math.sin(a), math.cos(a)
        r = S * 0.11
        circ = [(fx + px * r * 0.62 + math.cos(a) * r * 0.2, fy + py * r * 0.62 + math.sin(a) * r * 0.2),
                (fx - px * r * 0.62 + math.cos(a) * r * 0.2, fy - py * r * 0.62 + math.sin(a) * r * 0.2)]
        tri = [(cx + math.cos(a) * S * 0.02, cy + math.sin(a) * S * 0.02),
               (fx + px * r * 1.3, fy + py * r * 1.3), (fx - px * r * 1.3, fy - py * r * 1.3)]
        folhas.append((circ, r, tri, (fx, fy)))
    for circ, r, tri, _ in folhas:
        for c in circ:
            pygame.draw.circle(s, escuro, c, r + 5 * u)
        pygame.draw.polygon(s, escuro, tri, max(1, round(10 * u)))
    for circ, r, tri, _ in folhas:
        for c in circ:
            pygame.draw.circle(s, verde, c, r)
        pygame.draw.polygon(s, verde, tri)
    for _, _, _, centro in folhas:
        pygame.draw.line(s, claro, (cx, cy), centro, max(1, round(3 * u)))
    pygame.draw.circle(s, (40, 135, 50), (cx, cy), S * 0.04)
    return s


def _simbolo_sino(S):
    u = S / 176
    s = _sup(S)
    ouro, escuro, claro = (242, 190, 48), (150, 100, 15), (255, 240, 160)
    cx = S * 0.5
    pygame.draw.circle(s, escuro, (cx, S * 0.15), S * 0.075, max(1, round(8 * u)))
    corpo = [(S * 0.27, S * 0.66), (S * 0.29, S * 0.42), (S * 0.33, S * 0.30), (S * 0.41, S * 0.22), (S * 0.5, S * 0.20),
             (S * 0.59, S * 0.22), (S * 0.67, S * 0.30), (S * 0.71, S * 0.42), (S * 0.73, S * 0.66), (S * 0.86, S * 0.76),
             (S * 0.14, S * 0.76)]
    pygame.draw.polygon(s, ouro, corpo)
    pygame.draw.polygon(s, claro, [(S * 0.36, S * 0.33), (S * 0.42, S * 0.26), (S * 0.46, S * 0.27),
                                   (S * 0.41, S * 0.66), (S * 0.34, S * 0.66)])
    pygame.draw.polygon(s, escuro, corpo, max(1, round(7 * u)))
    pygame.draw.ellipse(s, escuro, (int(S * 0.12), int(S * 0.70), int(S * 0.76), int(S * 0.13)))
    pygame.draw.ellipse(s, (220, 165, 35), (int(S * 0.15), int(S * 0.715), int(S * 0.70), int(S * 0.09)))
    pygame.draw.circle(s, escuro, (cx, S * 0.85), S * 0.08)
    pygame.draw.circle(s, (205, 150, 30), (cx, S * 0.85), S * 0.055)
    return s


def _simbolo_diamante(S):
    u = S / 176
    s = _sup(S)
    t, m, b = S * 0.24, S * 0.42, S * 0.86
    pts = [(S * 0.30, t), (S * 0.70, t), (S * 0.88, m), (S * 0.50, b), (S * 0.12, m)]
    pygame.draw.polygon(s, (80, 200, 255), pts)
    pygame.draw.polygon(s, (195, 245, 255), [(S * 0.30, t), (S * 0.70, t), (S * 0.88, m), (S * 0.12, m)])
    pygame.draw.polygon(s, (140, 225, 255), [(S * 0.30, t), (S * 0.42, m), (S * 0.12, m)])
    pygame.draw.polygon(s, (140, 225, 255), [(S * 0.70, t), (S * 0.58, m), (S * 0.88, m)])
    pygame.draw.polygon(s, (40, 130, 210), [(S * 0.12, m), (S * 0.42, m), (S * 0.50, b)])
    pygame.draw.polygon(s, (65, 170, 240), [(S * 0.58, m), (S * 0.88, m), (S * 0.50, b)])
    borda = (20, 70, 140)
    l3, l2 = max(1, round(3 * u)), max(1, round(2 * u))
    pygame.draw.line(s, borda, (S * 0.12, m), (S * 0.88, m), l3)
    pygame.draw.line(s, borda, (S * 0.42, m), (S * 0.50, b), l3)
    pygame.draw.line(s, borda, (S * 0.58, m), (S * 0.50, b), l3)
    pygame.draw.line(s, borda, (S * 0.42, m), (S * 0.50, t), l2)
    pygame.draw.line(s, borda, (S * 0.58, m), (S * 0.50, t), l2)
    pygame.draw.polygon(s, borda, pts, max(1, round(6 * u)))
    bx, by = S * 0.30, S * 0.32
    pygame.draw.polygon(s, BRANCO, [(bx, by - 12 * u), (bx + 4 * u, by - 3 * u), (bx + 13 * u, by), (bx + 4 * u, by + 3 * u),
                                    (bx, by + 12 * u), (bx - 4 * u, by + 3 * u), (bx - 13 * u, by), (bx - 4 * u, by - 3 * u)])
    return s


def _simbolo_bau(S):
    u = S / 176
    s = _sup(S)
    madeira, escura, ouro, ouro_esc = (152, 92, 42), (80, 45, 18), (245, 200, 65), (165, 120, 25)
    tampa = pygame.Rect(int(S * 0.14), int(S * 0.24), int(S * 0.72), int(S * 0.24))
    corpo = pygame.Rect(int(S * 0.14), int(S * 0.47), int(S * 0.72), int(S * 0.35))
    raio = int(S * 0.13)
    m10 = round(10 * u)
    pygame.draw.rect(s, escura, tampa.inflate(m10, m10), border_top_left_radius=raio, border_top_right_radius=raio)
    pygame.draw.rect(s, (175, 108, 52), tampa, border_top_left_radius=raio, border_top_right_radius=raio)
    pygame.draw.rect(s, escura, corpo.inflate(m10, m10), border_radius=round(8 * u))
    pygame.draw.rect(s, madeira, corpo, border_radius=round(5 * u))
    for k in (0.36, 0.68):
        y = int(corpo.top + corpo.h * k)
        pygame.draw.line(s, escura, (corpo.left + 4 * u, y), (corpo.right - 4 * u, y), max(1, round(3 * u)))
    pygame.draw.line(s, escura, (tampa.left, tampa.bottom), (tampa.right, tampa.bottom), max(1, round(5 * u)))
    for k in (0.27, 0.73):
        faixa = pygame.Rect(int(S * k - S * 0.04), tampa.top + 2, int(S * 0.08), corpo.bottom - tampa.top - 2)
        pygame.draw.rect(s, ouro, faixa)
        pygame.draw.rect(s, ouro_esc, faixa, max(1, round(3 * u)))
    fech = pygame.Rect(int(S * 0.42), int(S * 0.40), int(S * 0.16), int(S * 0.17))
    pygame.draw.rect(s, ouro, fech, border_radius=round(5 * u))
    pygame.draw.rect(s, ouro_esc, fech, max(1, round(3 * u)), border_radius=round(5 * u))
    pygame.draw.circle(s, (30, 20, 10), (fech.centerx, fech.centery - 4 * u), 6 * u)
    pygame.draw.rect(s, (30, 20, 10), (fech.centerx - 3 * u, fech.centery - 2 * u, 6 * u, 12 * u))
    return s


def _simbolo_texto(S, txt, fonte, cor, contorno, borda_ext):
    u = S / 176
    s = _sup(S)
    img = fonte.render(txt, True, cor)
    cont = fonte.render(txt, True, contorno)
    ext = fonte.render(txt, True, borda_ext)
    r = img.get_rect(center=(S // 2, S // 2 + int(S * 0.02)))
    for ang in range(0, 360, 20):
        dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        s.blit(ext, r.move(dx * 11 * u, dy * 11 * u))
    for ang in range(0, 360, 24):
        dx, dy = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        s.blit(cont, r.move(dx * 6 * u, dy * 6 * u))
    s.blit(img, r)
    return s


def criar_simbolo(nome, S, fonte_grande):
    if nome == "limao":
        return _simbolo_limao(S)
    if nome == "cereja":
        return _simbolo_cereja(S)
    if nome == "trevo":
        return _simbolo_trevo(S)
    if nome == "sino":
        return _simbolo_sino(S)
    if nome == "diamante":
        return _simbolo_diamante(S)
    if nome == "bau":
        return _simbolo_bau(S)
    if nome == "sete":
        return _simbolo_texto(S, "7", fonte_grande, (232, 36, 44), (255, 205, 60), (90, 10, 10))
    return _simbolo_texto(S, "6", fonte_grande, (150, 0, 10), (40, 0, 0), (255, 60, 40))   # seis do diabo


def borrar(img, k):
    """Versão "em movimento" do símbolo, para quando o rolo gira rápido."""
    w, h = img.get_size()
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    copia = img.copy()
    copia.set_alpha(70)
    for dy in (-18, -9, 0, 9, 18):
        s.blit(copia, (0, round(dy * k)))
    return s


def superficie_degrade(w, h, c1, c2, raio=0):
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        pygame.draw.line(s, (*misturar(c1, c2, y / max(1, h - 1)), 255), (0, y), (w, y))
    if raio:
        mascara = pygame.Surface((w, h), pygame.SRCALPHA)
        pygame.draw.rect(mascara, (255, 255, 255, 255), (0, 0, w, h), border_radius=raio)
        s.blit(mascara, (0, 0), special_flags=pygame.BLEND_RGBA_MULT)
    return s


def sombra_rolo(w, h, k):
    """Sombra curva por cima dos rolos (dá a impressão de cilindro)."""
    s = pygame.Surface((w, h), pygame.SRCALPHA)
    for y in range(h):
        d = min(y, h - 1 - y) / (h * 0.30)
        a = int(165 * max(0.0, 1 - d) ** 2)
        pygame.draw.line(s, (10, 5, 0, a), (0, y), (w, y))
    faixa = max(1, round(10 * k))
    for x in range(faixa):
        pygame.draw.line(s, (255, 255, 255, int(30 * (1 - x / faixa))), (x + round(6 * k), 0), (x + round(6 * k), h))
    return s


def criar_vinheta(cor, forca, W, H):
    pw, ph = 160, 90
    p = pygame.Surface((pw, ph), pygame.SRCALPHA)
    for y in range(ph):
        for x in range(pw):
            dx = (x + 0.5) / pw * 2 - 1
            dy = (y + 0.5) / ph * 2 - 1
            d = math.sqrt(dx * dx + dy * dy) / math.sqrt(2)
            a = limitar((d - 0.35) / 0.65, 0.0, 1.0) ** 1.6 * forca
            p.set_at((x, y), (*cor, int(a)))
    return pygame.transform.smoothscale(p, (W, H))


# ---------- áreas da tela (coordenadas lógicas, 1280x720) ----------
R_MAQUINA = (372, 64, 536, 480)
R_LETREIRO = (392, 74, 496, 60)
R_JANELA = (REEL_X - 10, REEL_Y - 10, REEL_W + 20, REEL_H + 20)
R_LED_GIROS = (404, 452, 150, 44)
R_GIRAR = (566, 452, 148, 44)
R_LED_PREMIO = (726, 452, 150, 44)
PIVO_ALAVANCA = (928, 300)
R_TELEFONE = (56, 82, 228, 176)
R_QUADRO = (20, 268, 320, 276)
R_CAIXA = (944, 64, 316, 270)
R_TELA_CAIXA = (964, 106, 276, 112)
R_LOJA = (944, 346, 316, 198)
R_PRATELEIRA = (296, 588, 688, 120)
R_BOLSO = (16, 588, 268, 120)
R_MENU_HUD = (996, 588, 268, 120)


def pos_amuleto(i):
    return pygame.Rect(308 + i * 84, 604, 76, 76)


class Pincel:
    """Desenha usando coordenadas lógicas numa superfície de qualquer tamanho (fator k)."""

    def __init__(self, sup, k):
        self.s = sup
        self.k = k

    def R(self, rect):
        x, y, w, h = rect
        k = self.k
        x0, y0 = round(x * k), round(y * k)
        return pygame.Rect(x0, y0, max(1, round((x + w) * k) - x0), max(1, round((y + h) * k) - y0))

    def P(self, p):
        return (p[0] * self.k, p[1] * self.k)

    def L(self, v):
        return max(1, round(v * self.k))

    def rect(self, cor, rect, larg=0, raio=0):
        pygame.draw.rect(self.s, cor, self.R(rect), self.L(larg) if larg else 0, border_radius=round(raio * self.k))

    def circulo(self, cor, c, raio, larg=0):
        pygame.draw.circle(self.s, cor, self.P(c), raio * self.k, self.L(larg) if larg else 0)

    def linha(self, cor, a, b, larg=1):
        pygame.draw.line(self.s, cor, self.P(a), self.P(b), self.L(larg))

    def degrade(self, rect, c1, c2, raio=0):
        r = self.R(rect)
        self.s.blit(superficie_degrade(r.w, r.h, c1, c2, round(raio * self.k)), r.topleft)

    def sombra(self, rect, alpha):
        r = self.R(rect)
        s = pygame.Surface(r.size, pygame.SRCALPHA)
        pygame.draw.ellipse(s, (0, 0, 0, alpha), s.get_rect())
        self.s.blit(s, r.topleft)

    def imagem(self, img, pos):
        self.s.blit(img, (round(pos[0] * self.k), round(pos[1] * self.k)))


def criar_fundo(k):
    """Cenário fixo, desenhado com o dobro da resolução e depois reduzido (bordas lisas)."""
    ss = 2
    W, H = round(LARGURA * k), round(ALTURA * k)
    grande = pygame.Surface((W * ss, H * ss))
    pc = Pincel(grande, k * ss)
    K = pc.k
    rnd = random.Random(11)
    grande.fill((18, 16, 20))
    h, w = 34, 80
    for lin in range(0, 600 // h + 1):
        y = lin * h
        des = 0 if lin % 2 == 0 else w // 2
        for x in range(-des, LARGURA, w):
            v = rnd.randint(-7, 7)
            base = (52 + v, 42 + v, 45 + v)
            pc.rect(base, (x + 2, y + 2, w - 4, h - 4), raio=3)
            pc.linha(clarear(base, 0.08), (x + 4, y + 3.5), (x + w - 6, y + 3.5), 1)
            if rnd.random() < 0.25:
                pc.rect(escurecer(base, 0.8), (x + rnd.randint(6, 40), y + rnd.randint(6, 18),
                                               rnd.randint(8, 30), rnd.randint(4, 10)), raio=3)
    for _ in range(16):
        x = rnd.randint(0, LARGURA)
        comp = rnd.randint(80, 320)
        larg = rnd.randint(6, 20)
        y0 = rnd.randint(0, 220)
        mancha = pygame.Surface((max(1, round(larg * K)), max(1, round(comp * K))), pygame.SRCALPHA)
        mh = mancha.get_height()
        for yy in range(mh):
            pygame.draw.line(mancha, (8, 14, 8, int(60 * (1 - yy / mh))), (0, yy), (mancha.get_width(), yy))
        pc.imagem(mancha, (x, y0))
    # chão
    pc.rect((24, 23, 25), (0, 566, LARGURA, ALTURA - 566))
    for _ in range(50):
        x, y = rnd.randint(0, LARGURA), rnd.randint(572, ALTURA)
        pc.linha((16, 15, 17), (x, y), (x + rnd.randint(-60, 60), y + rnd.randint(-8, 8)), 1)
    pc.rect((10, 9, 11), (0, 560, LARGURA, 8))

    _desenhar_maquina_fixa(pc)
    _desenhar_caixa_fixo(pc)
    _desenhar_telefone_fixo(pc)
    _desenhar_quadro_fixo(pc, rnd)
    _desenhar_paineis_fixos(pc)
    return pygame.transform.smoothscale(grande, (W, H))


def _desenhar_maquina_fixa(pc):
    x, y, w, h = R_MAQUINA
    pc.sombra((x - 30, y + h - 30, w + 60, 60), 120)
    pc.degrade((x, y, w, h), (150, 24, 36), (70, 8, 16), 26)
    for kx in (0.04, 0.96):         # laterais mais escuras
        pc.degrade((x + w * kx - 9, y + 20, 18, h - 40), (100, 14, 24), (50, 6, 12), 8)
    pc.rect((230, 180, 60), (x, y, w, h), 5, 26)
    pc.rect((95, 60, 20), (x + 7, y + 7, w - 14, h - 14), 2, 22)
    # letreiro
    pc.rect((24, 6, 10), R_LETREIRO, raio=12)
    pc.rect((230, 180, 60), R_LETREIRO, 3, 12)
    # janela dos rolos
    pc.rect((18, 18, 22), R_JANELA, raio=12)
    pc.rect((210, 165, 70), R_JANELA, 4, 12)
    for c in range(COLUNAS):
        pc.degrade((REEL_X + c * PASSO, REEL_Y, CEL, REEL_H), (246, 240, 224), (222, 212, 190))
    # painel de baixo
    pc.rect((38, 10, 16), (394, 446, 492, 88), raio=10)
    for r in (R_LED_GIROS, R_LED_PREMIO):
        pc.rect((6, 4, 4), r, raio=6)
        pc.rect((110, 25, 25), r, 2, 6)
    # bandeja de moedas e pés
    pc.rect((28, 28, 32), (560, 536, 160, 22), raio=6)
    pc.rect((90, 90, 100), (560, 536, 160, 22), 2, 6)
    for px in (400, 860):
        pc.rect((30, 26, 28), (px, y + h - 2, 24, 18), raio=4)
    # suporte da alavanca
    pc.rect((70, 70, 80), (906, 266, 28, 70), raio=7)
    pc.rect((140, 140, 150), (906, 266, 28, 70), 2, 7)
    for by in (276, 326):
        pc.circulo((170, 170, 180), (920, by), 3)


def _desenhar_caixa_fixo(pc):
    x, y, w, h = R_CAIXA
    pc.sombra((x - 10, y + h - 18, w + 20, 36), 90)
    pc.degrade((x, y, w, h), (92, 98, 112), (48, 52, 62), 14)
    pc.rect((150, 160, 178), (x, y, w, h), 3, 14)
    pc.rect((170, 28, 34), (x + 14, y + 8, w - 28, 26), raio=6)
    tx, ty, tw, th = R_TELA_CAIXA
    pc.rect((18, 20, 24), (tx - 8, ty - 8, tw + 16, th + 16), raio=8)
    pc.rect((5, 26, 14), R_TELA_CAIXA, raio=4)


def _desenhar_telefone_fixo(pc):
    x, y, w, h = R_TELEFONE
    pc.rect((68, 44, 28), R_TELEFONE, raio=10)
    pc.rect((40, 25, 15), R_TELEFONE, 3, 10)
    for px, py in ((x + 12, y + 12), (x + w - 12, y + 12), (x + 12, y + h - 12), (x + w - 12, y + h - 12)):
        pc.circulo((150, 140, 120), (px, py), 4)
    pc.degrade((82, 116, 176, 128), (125, 18, 26), (65, 8, 14), 20)
    pc.rect((35, 5, 8), (82, 116, 176, 128), 3, 20)
    cx, cy = 170, 184
    pc.circulo((228, 218, 192), (cx, cy), 46)
    pc.circulo((60, 10, 15), (cx, cy), 46, 4)
    for i in range(10):
        a = math.radians(-60 + i * 28)
        pc.circulo((45, 12, 16), (cx + math.cos(a) * 30, cy + math.sin(a) * 30), 7)
    pc.circulo((150, 20, 28), (cx, cy), 14)
    for gx in (100, 228):
        pc.rect((40, 6, 10), (gx, 104, 14, 16), raio=3)


def _desenhar_quadro_fixo(pc, rnd):
    pc.rect((105, 68, 36), R_QUADRO, raio=8)
    pc.rect((60, 38, 18), R_QUADRO, 3, 8)
    lousa = (R_QUADRO[0] + 12, R_QUADRO[1] + 12, R_QUADRO[2] - 24, R_QUADRO[3] - 24)
    pc.rect((30, 50, 40), lousa, raio=4)
    r = pc.R(lousa)
    K = pc.k
    marcas = pygame.Surface(r.size, pygame.SRCALPHA)
    for _ in range(26):
        x, y = rnd.randint(0, lousa[2]), rnd.randint(0, lousa[3])
        pygame.draw.line(marcas, (220, 230, 220, 14), (x * K, y * K),
                         ((x + rnd.randint(-70, 70)) * K, (y + rnd.randint(-10, 10)) * K), max(1, round(rnd.randint(4, 12) * K)))
    pc.s.blit(marcas, r.topleft)
    pc.rect((90, 58, 30), (R_QUADRO[0] + 30, R_QUADRO[1] + R_QUADRO[3] - 10, 60, 6), raio=3)


def _desenhar_paineis_fixos(pc):
    # loja
    pc.rect((46, 32, 24), R_LOJA, raio=12)
    pc.rect((125, 88, 52), R_LOJA, 3, 12)
    pc.rect((78, 55, 34), (R_LOJA[0] + 8, R_LOJA[1] + 178, R_LOJA[2] - 16, 8), raio=3)
    # prateleira dos amuletos
    pc.rect((38, 28, 22), R_PRATELEIRA, raio=12)
    pc.rect((110, 80, 50), R_PRATELEIRA, 3, 12)
    for i in range(MAX_ESPACOS):
        pc.rect((24, 18, 14), pos_amuleto(i), raio=10)
    # bolso e menu
    for r in (R_BOLSO, R_MENU_HUD):
        pc.rect((22, 22, 28), r, raio=12)
        pc.rect((80, 85, 100), r, 2, 12)


# =====================================================================
# PEÇAS ANIMADAS (tudo em coordenadas lógicas)
# =====================================================================
class Rolo:
    """Uma coluna do caça-níquel."""

    def __init__(self, col):
        self.col = col
        self.simbolos = [random.choice(SIMBOLOS) for _ in range(LINHAS)]
        self.estado = "parado"
        self.t = 0.0
        self.desloc = 0.0
        self.vel = 0.0
        self.parar_em = 0.0
        self.finais = None
        self.fita = list(SIMBOLOS)
        self.t_assentar = 0.0

    def girar(self, finais, parar_em, fita):
        self.estado = "girando"
        self.t = 0.0
        self.desloc = 0.0
        self.vel = 0.0
        self.finais = finais
        self.parar_em = parar_em
        self.fita = fita

    def atualizar(self, dt):
        """Devolve True no quadro em que o rolo para."""
        if self.estado == "girando":
            self.t += dt
            self.vel = min(2600.0, self.vel + 9000 * dt)
            self.desloc += self.vel * dt
            if self.t >= self.parar_em:
                self.estado = "assentando"
                self.simbolos = list(self.finais)
                self.t_assentar = 0.0
                return True
        elif self.estado == "assentando":
            self.t_assentar += dt
            if self.t_assentar >= 0.25:
                self.estado = "parado"
        return False

    def deslocamento(self):
        if self.estado != "assentando":
            return 0.0
        p = self.t_assentar / 0.25
        return -34 * (1 - p) ** 3 + 9 * math.sin(p * math.pi) * (1 - p)


class Flutuante:
    __slots__ = ("sup", "x", "y", "vy", "vida", "total")

    def __init__(self, sup, x, y, vida=1.0, vy=-45):
        self.sup, self.x, self.y, self.vy = sup, x, y, vy
        self.vida = self.total = vida


class Particula:
    __slots__ = ("x", "y", "vx", "vy", "vida", "total", "tam", "cor", "gravidade", "brilha")

    def __init__(self, x, y, vx, vy, vida, tam, cor, gravidade=0.0, brilha=False):
        self.x, self.y, self.vx, self.vy = x, y, vx, vy
        self.vida = self.total = vida
        self.tam, self.cor, self.gravidade, self.brilha = tam, cor, gravidade, brilha


class MoedaVoo:
    __slots__ = ("a", "b", "atraso", "t", "dur", "altura", "som")

    def __init__(self, a, b, atraso, dur, altura, som=True):
        self.a, self.b, self.atraso, self.dur, self.altura, self.som = a, b, atraso, dur, altura, som
        self.t = 0.0


def _nivel(v, passos=4):
    """Arredonda um valor de 0 a 1 em poucos degraus (para reaproveitar desenhos)."""
    return round(limitar(v, 0.0, 1.0) * passos) / passos


# =====================================================================
# O JOGO
# =====================================================================
class Jogo:
    def __init__(self):
        ativar_nitidez()
        os.environ.setdefault("SDL_VIDEO_CENTERED", "1")
        pygame.mixer.pre_init(22050, -16, 2, 512)
        pygame.init()
        pygame.display.set_caption(TITULO)
        self.relogio = pygame.time.Clock()
        self.k = 1.0
        self.ox = self.oy = 0
        self._limpar_caches()
        self.abrir_janela(False)
        self.mensagem_tela("Preparando a máquina...")
        self.sons = Sons()
        self.recriar_recursos()

        self.recorde = carregar_recorde()
        self.estado = "menu"
        self.modal = None
        self.p = None
        self.rolos = [Rolo(c) for c in range(COLUNAS)]
        self.velocidade = 1
        self.sair = False
        self.tempo = 0.0
        self.mouse = (0, 0)
        self.pos_alavanca = pygame.Rect(0, 0, 1, 1)
        self.limpar_efeitos()
        self.sons.ambiente(True)

    # -----------------------------------------------------------------
    # Janela, escala e recursos
    # -----------------------------------------------------------------
    def _limpar_caches(self):
        self._fontes = {}
        self._cache_txt = {}
        self._caixas = {}
        self._icones = {}
        self._sprites = {}
        _cache_brilho.clear()

    def abrir_janela(self, tela_cheia):
        self.tela_cheia = tela_cheia
        try:
            dw, dh = pygame.display.get_desktop_sizes()[0]
        except Exception:
            dw, dh = LARGURA, ALTURA
        if tela_cheia:
            self.tela = pygame.display.set_mode((dw, dh), pygame.FULLSCREEN)
            tw, th = self.tela.get_size()
            self.k = min(tw / LARGURA, th / ALTURA)
        else:
            forcado = os.environ.get("GAMBLER_ESCALA")
            if forcado:
                self.k = float(forcado)
            else:
                k = min(dw * 0.94 / LARGURA, (dh - 80) * 0.92 / ALTURA)
                self.k = max(0.5, math.floor(k * 20) / 20)
            self.tela = pygame.display.set_mode((round(LARGURA * self.k), round(ALTURA * self.k)))
        W, H = round(LARGURA * self.k), round(ALTURA * self.k)
        tw, th = self.tela.get_size()
        self.ox, self.oy = (tw - W) // 2, (th - H) // 2
        self.cena = pygame.Surface((W, H)).convert()

    def mensagem_tela(self, texto):
        self.tela.fill(PRETO)
        f = pygame.font.SysFont(FONTES["ui"], max(10, round(28 * self.k)), bold=True)
        img = f.render(texto, True, (200, 200, 200))
        self.tela.blit(img, img.get_rect(center=(self.tela.get_width() // 2, self.tela.get_height() // 2)))
        pygame.display.flip()

    def recriar_recursos(self):
        """Gera todas as imagens no tamanho real da janela."""
        self._limpar_caches()
        k = self.k
        cel = self.px(CEL)
        fonte_grande = pygame.font.SysFont(FONTES["titulo"], max(8, round(cel * 2 * 0.95)))
        self.img = {}
        for s in SIMBOLOS + ["seis"]:
            grande = criar_simbolo(s, cel * 2, fonte_grande)
            self.img[s] = pygame.transform.smoothscale(grande, (cel, cel)).convert_alpha()
        self.img_borrada = {s: borrar(i, k).convert_alpha() for s, i in self.img.items()}
        mini, media = self.px(40), self.px(64)
        self.img_mini = {s: pygame.transform.smoothscale(i, (mini, mini)).convert_alpha() for s, i in self.img.items()}
        self.img_media = {s: pygame.transform.smoothscale(i, (media, media)).convert_alpha() for s, i in self.img.items()}
        self.sombra_rolo = sombra_rolo(cel, self.px(REEL_H), k).convert_alpha()
        self.fundo = criar_fundo(k).convert()
        W, H = self.cena.get_size()
        self.vinheta = criar_vinheta((0, 0, 0), 235, W, H).convert_alpha()
        self.sup_escura = pygame.Surface((W, H)).convert()
        self.sup_escura.fill(PRETO)
        self.sup_vermelha = pygame.Surface((W, H)).convert()
        self.sup_vermelha.fill((200, 0, 0))
        self.sup_branca = pygame.Surface((W, H)).convert()
        self.sup_branca.fill(BRANCO)
        self.faixa_anuncio = pygame.Surface((W, self.px(96))).convert()
        self.faixa_anuncio.fill(PRETO)
        tela = self.ret(R_TELA_CAIXA)
        linhas = pygame.Surface(tela.size, pygame.SRCALPHA)
        passo = max(2, round(3 * k))
        for yy in range(0, tela.h, passo):
            pygame.draw.line(linhas, (0, 0, 0, 80), (0, yy), (tela.w, yy))
        self.linhas_caixa = linhas.convert_alpha()

    def alternar_tela_cheia(self):
        self.mensagem_tela("Ajustando a tela...")
        self.abrir_janela(not self.tela_cheia)
        self.mensagem_tela("Ajustando a tela...")
        self.recriar_recursos()

    # ---------- conversões entre coordenadas lógicas e pixels ----------
    def px(self, v):
        return max(1, int(round(v * self.k)))

    def pt(self, x, y):
        return (x * self.k, y * self.k)

    def ret(self, rect):
        x, y, w, h = rect
        k = self.k
        x0, y0 = round(x * k), round(y * k)
        return pygame.Rect(x0, y0, max(1, round((x + w) * k) - x0), max(1, round((y + h) * k) - y0))

    def para_logico(self, pos):
        return (int((pos[0] - self.ox) / self.k), int((pos[1] - self.oy) / self.k))

    # -----------------------------------------------------------------
    # Desenho básico (sempre em coordenadas lógicas)
    # -----------------------------------------------------------------
    def blit(self, img, pos, ancora="topleft", flags=0):
        r = img.get_rect(**{ancora: (round(pos[0] * self.k), round(pos[1] * self.k))})
        self.cena.blit(img, r, special_flags=flags)
        return r

    def brilhar(self, cor, centro, raio):
        """Luz suave (somada à imagem)."""
        self.blit(brilho(cor, raio * self.k), centro, "center", pygame.BLEND_ADD)

    def circulo(self, cor, centro, raio, larg=0):
        rr = max(0.6, raio * self.k)
        if larg:
            pygame.draw.aacircle(self.cena, cor, self.pt(*centro), rr, max(1, round(larg * self.k)))
        else:
            pygame.draw.aacircle(self.cena, cor, self.pt(*centro), rr)

    def linha(self, cor, a, b, larg=1):
        pygame.draw.aaline(self.cena, cor, self.pt(*a), self.pt(*b), max(1, round(larg * self.k)))

    def linhas(self, cor, pts, larg):
        for a, b in zip(pts, pts[1:]):
            self.linha(cor, a, b, larg)
        for p in pts:
            self.circulo(cor, p, larg / 2)

    def caixa_img(self, w, h, cor, raio=10, borda=None, larg=2, alpha=255, alpha_borda=235):
        """Retângulo arredondado liso (desenhado 3x maior e reduzido). Fica guardado."""
        chave = (round(w, 1), round(h, 1), tuple(cor), raio, tuple(borda) if borda else None, larg, alpha, alpha_borda)
        img = self._caixas.get(chave)
        if img is None:
            W, H = self.px(w), self.px(h)
            ss = 3
            s = pygame.Surface((W * ss, H * ss), pygame.SRCALPHA)
            s.fill((*(borda or cor), 0))
            rr = round(raio * self.k * ss)
            if alpha > 0:
                pygame.draw.rect(s, (*cor, alpha), (0, 0, W * ss, H * ss), border_radius=rr)
            if borda:
                pygame.draw.rect(s, (*borda, alpha_borda), (0, 0, W * ss, H * ss), max(1, round(larg * self.k * ss)), border_radius=rr)
            img = pygame.transform.smoothscale(s, (W, H)).convert_alpha()
            if len(self._caixas) > 700:
                self._caixas.clear()
            self._caixas[chave] = img
        return img

    def caixa(self, rect, cor, raio=10, borda=None, larg=2, alpha=255, alpha_borda=235):
        x, y, w, h = rect
        self.cena.blit(self.caixa_img(w, h, cor, raio, borda, larg, alpha, alpha_borda), (round(x * self.k), round(y * self.k)))

    # ---------- textos ----------
    def fonte_px(self, tipo, px, negrito=False):
        chave = (tipo, px, negrito)
        f = self._fontes.get(chave)
        if f is None:
            try:
                f = pygame.font.SysFont(FONTES[tipo], px, bold=negrito)
            except Exception:
                f = pygame.font.Font(None, px)
            self._fontes[chave] = f
        return f

    def fonte(self, tam, tipo="ui", negrito=True):
        return self.fonte_px(tipo, max(6, int(round(tam * self.k))), negrito)

    def render(self, txt, tam, cor, tipo="ui", negrito=True):
        chave = (txt, tam, tuple(cor), tipo, negrito)
        s = self._cache_txt.get(chave)
        if s is None:
            if len(self._cache_txt) > 900:
                self._cache_txt.clear()
            s = self.fonte(tam, tipo, negrito).render(txt, True, cor).convert_alpha()
            self._cache_txt[chave] = s
        return s

    def escrever(self, txt, tam, cor, pos, ancora="center", tipo="ui", negrito=True, sombra=2):
        s = self.render(txt, tam, cor, tipo, negrito)
        r = s.get_rect(**{ancora: (round(pos[0] * self.k), round(pos[1] * self.k))})
        if sombra:
            d = max(1, round(sombra * self.k))
            self.cena.blit(self.render(txt, tam, PRETO, tipo, negrito), (r.x + d, r.y + d))
        self.cena.blit(s, r)
        k = self.k
        return pygame.Rect(int(r.x / k), int(r.y / k), int(math.ceil(r.w / k)), int(math.ceil(r.h / k)))

    def texto_sombra(self, txt, tam, cor, tipo="ui"):
        f = self.fonte(tam, tipo, True)
        s = f.render(txt, True, cor)
        d = max(1, round(3 * self.k))
        sup = pygame.Surface((s.get_width() + d, s.get_height() + d), pygame.SRCALPHA)
        sup.blit(f.render(txt, True, PRETO), (d, d))
        sup.blit(s, (0, 0))
        return sup

    def quebrar(self, texto, tam, largura, tipo="ui", negrito=False):
        f = self.fonte(tam, tipo, negrito)
        limite = largura * self.k
        linhas = []
        for par in texto.split("\n"):
            atual = ""
            for palavra in par.split(" "):
                teste = (atual + " " + palavra).strip()
                if f.size(teste)[0] <= limite or not atual:
                    atual = teste
                else:
                    linhas.append(atual)
                    atual = palavra
            linhas.append(atual)
        return linhas

    # ---------- ícones e pequenos desenhos ----------
    def _cracha(self, tam, cor, glifo, cor_glifo, fonte_tipo="simbolo", escala_glifo=0.56):
        """Quadradinho arredondado com um símbolo no meio, desenhado em alta e reduzido."""
        P = self.px(tam)
        ss = 2
        S = P * ss
        g = pygame.Surface((S, S), pygame.SRCALPHA)
        g.fill((*cor, 0))
        raio = S // 5
        pygame.draw.rect(g, (*escurecer(cor, 0.22), 255), (0, 0, S, S), border_radius=raio)
        pygame.draw.rect(g, (*cor, 255), (0, 0, S, S), max(2, round(3 * self.k * ss)), border_radius=raio)
        f = self.fonte_px(fonte_tipo, max(6, int(S * escala_glifo)))
        gl = f.render(glifo, True, cor_glifo)
        g.blit(gl, gl.get_rect(center=(S // 2, S // 2 + ss)))
        return pygame.transform.smoothscale(g, (P, P)).convert_alpha()

    def icone_amuleto(self, aid, tam):
        chave = ("amuleto", aid, tam)
        s = self._icones.get(chave)
        if s is None:
            a = AMULETOS[aid]
            cor = RARIDADES[a["rar"]]["cor"]
            if a["icone"] == "7":
                s = self._cracha(tam, cor, "7", (240, 50, 50), "titulo", 0.75)
            else:
                s = self._cracha(tam, cor, a["icone"], clarear(cor, 0.35))
            self._icones[chave] = s
        return s

    def icone_generico(self, codigo, tam, cor):
        """Ícone de uma oferta do telefone: símbolo da máquina, amuleto ou glifo."""
        if codigo.startswith("amuleto:"):
            return self.icone_amuleto(codigo[8:], tam)
        chave = ("generico", codigo, tam, tuple(cor))
        s = self._icones.get(chave)
        if s is None:
            if codigo.startswith("simbolo:"):
                P = self.px(tam)
                s = pygame.transform.smoothscale(self.img[codigo[8:]], (P, P)).convert_alpha()
            else:
                s = self._cracha(tam, cor, codigo, clarear(cor, 0.4))
            self._icones[chave] = s
        return s

    def sprite_moeda(self, r):
        chave = ("moeda", r)
        s = self._sprites.get(chave)
        if s is None:
            ss = 3
            tam = max(4, int(math.ceil((r + 3) * 2 * self.k)))
            T = tam * ss
            K = self.k * ss
            g = pygame.Surface((T, T), pygame.SRCALPHA)
            g.fill((250, 200, 50, 0))
            c = T / 2
            pygame.draw.circle(g, (150, 105, 15), (c, c), (r + 2) * K)
            pygame.draw.circle(g, (250, 200, 50), (c, c), r * K)
            pygame.draw.circle(g, (215, 160, 30), (c, c), r * K * 0.72, max(1, round(K)))
            pygame.draw.circle(g, (255, 235, 140), (c - r * K * 0.3, c - r * K * 0.3), r * K * 0.32)
            s = pygame.transform.smoothscale(g, (tam, tam)).convert_alpha()
            self._sprites[chave] = s
        return s

    def moeda(self, x, y, r=9):
        self.blit(self.sprite_moeda(r), (x, y), "center")

    def sprite_bilhete(self, l, a):
        chave = ("bilhete", l, a)
        s = self._sprites.get(chave)
        if s is None:
            ss = 3
            W, H = self.px(l + 4), self.px(a + 4)
            K = self.k * ss
            g = pygame.Surface((W * ss, H * ss), pygame.SRCALPHA)
            g.fill((255, 175, 60, 0))
            r = pygame.Rect(round(2 * K), round(2 * K), round(l * K), round(a * K))
            pygame.draw.rect(g, (255, 175, 60), r, border_radius=round(3 * K))
            pygame.draw.rect(g, (150, 80, 20), r, max(1, round(2 * K)), border_radius=round(3 * K))
            for x in (r.left, r.right):
                pygame.draw.circle(g, (40, 25, 15), (x, r.centery), 3 * K)
            pygame.draw.line(g, (150, 80, 20), (r.centerx, r.top + 3 * K), (r.centerx, r.bottom - 3 * K), max(1, round(K)))
            s = pygame.transform.smoothscale(g, (W, H)).convert_alpha()
            self._sprites[chave] = s
        return s

    def bilhete(self, x, y, l=26, a=16):
        self.blit(self.sprite_bilhete(l, a), (x, y), "center")

    # -----------------------------------------------------------------
    # Botões (redesenhados a cada quadro, em coordenadas lógicas)
    # -----------------------------------------------------------------
    def botao(self, rect, texto, acao, ativo=True, cor=(60, 64, 78), cor_texto=BRANCO, tam=18, destaque=False, dica=None):
        r = pygame.Rect(rect)
        hover = ativo and r.collidepoint(self.mouse)
        base = cor if ativo else (42, 42, 48)
        if hover:
            base = clarear(base, 0.18)
        self.caixa((r.x, r.y + 3, r.w, r.h), escurecer(base, 0.45), 9)
        borda = clarear(base, 0.35) if ativo else (62, 62, 70)
        if destaque and ativo:
            borda = misturar(OURO, BRANCO, _nivel(0.5 + 0.5 * math.sin(self.tempo * 6), 5))
            self.caixa((r.x - 3, r.y - 3, r.w + 6, r.h + 6), borda, 11, borda, 2, alpha=0)
        self.caixa(r, base, 9, borda, 2)
        linhas = texto.split("\n")
        alt = tam + 4
        y0 = r.centery - (len(linhas) - 1) * alt / 2
        for i, linha in enumerate(linhas):
            cor_l = cor_texto if ativo else (110, 110, 118)
            self.escrever(linha, tam if i == 0 else max(12, tam - 4), cor_l, (r.centerx, y0 + i * alt), sombra=1)
        self.botoes.append((r, acao, ativo))
        if dica:
            self.dicas.append((r, dica))
        return r

    # -----------------------------------------------------------------
    # Efeitos
    # -----------------------------------------------------------------
    def limpar_efeitos(self):
        self.agenda = []
        self.flutuantes = []
        self.particulas = []
        self.voos = []
        self.destaques = []
        self.pulsos = {}
        self.anuncio = None
        self.texto_grande = None
        self.tremor = 0.0
        self.flash_vermelho = 0.0
        self.flash_branco = 0.0
        self.aviso_txt = None
        self.alavanca = 0.0
        self.alavanca_t = -1.0
        self.premio_led = 0
        self.giro = None
        self.fase = "pacote"
        self.ofertas = []
        self.ligacao_maldita = False
        self.timer_toque = 0.0
        self.timer_tick = 0.0
        self.suspense_tocado = True
        self.timer_demo = 1.0
        self.luz = 1.0
        self.timer_piscar = random.uniform(5, 10)
        self.piscando = 0.0
        self.t_queda = 0.0
        self.t_fim = 0.0
        self.botoes = []
        self.dicas = []
        self.direito = []
        self.novo_recorde = False
        self.contagem = {"bolso": 0.0, "caixa": 0.0, "bilhetes": 0.0}

    def agendar(self, atraso, funcao):
        self.agenda.append([atraso, funcao])

    def atualizar_agenda(self, dt):
        if not self.agenda:
            return
        for item in self.agenda:
            item[0] -= dt
        prontos = sorted((it for it in self.agenda if it[0] <= 0), key=lambda it: it[0])
        self.agenda = [it for it in self.agenda if it[0] > 0]
        for _, f in prontos:
            f()

    def anunciar(self, texto, sub="", cor=BRANCO, dur=2.0):
        self.anuncio = {"texto": texto, "sub": sub, "cor": cor, "t": dur, "dur": dur}

    def avisar(self, texto, cor=LARANJA):
        self.aviso_txt = (texto, cor, 2.5)

    def flutuar(self, texto, x, y, cor=OURO, tam=26, vida=1.1, vy=-50):
        self.flutuantes.append(Flutuante(self.texto_sombra(texto, tam, cor), x, y, vida, vy))
        if len(self.flutuantes) > 40:
            del self.flutuantes[0]

    def faiscas(self, x, y, cor, n=12, vel=220, vida=0.6, tam=4, gravidade=300, brilha=True):
        for _ in range(n):
            a = random.uniform(0, math.tau)
            v = random.uniform(0.3, 1.0) * vel
            self.particulas.append(Particula(x, y, math.cos(a) * v, math.sin(a) * v - vel * 0.3, vida * random.uniform(0.6, 1.2),
                                             tam * random.uniform(0.6, 1.3), cor, gravidade, brilha))
        if len(self.particulas) > 700:
            del self.particulas[:len(self.particulas) - 700]

    def voar_moedas(self, a, b, n, dur=0.7, altura=120, som=True):
        n = max(1, min(30, n))
        for i in range(n):
            ax = a[0] + random.uniform(-20, 20)
            ay = a[1] + random.uniform(-8, 8)
            self.voos.append(MoedaVoo((ax, ay), b, i * 0.035, dur * random.uniform(0.85, 1.15), altura * random.uniform(0.6, 1.2), som))

    def som(self, nome, volume=1.0, intervalo=0.0):
        self.sons.tocar(nome, volume, intervalo)

    # -----------------------------------------------------------------
    # Partida: começo, giros, rodadas e prazos
    # -----------------------------------------------------------------
    def nova_partida(self):
        self.limpar_efeitos()
        self.p = Partida()
        self.estado = "jogo"
        self.modal = None
        self.fase = "pacote"
        self.contagem = {"bolso": float(self.p.bolso), "caixa": float(self.p.caixa), "bilhetes": float(self.p.bilhetes)}
        self.anunciar("PRAZO 1", f"Pague {formatar(self.p.divida)} moedas no caixa em 3 rodadas", OURO, 3.2)
        self.som("juros")

    def pode_mexer(self):
        return self.estado == "jogo" and self.modal is None and self.fase in ("pacote", "pronto", "telefone")

    def escolher_pacote(self, i):
        if self.estado != "jogo" or self.modal or self.fase != "pacote":
            return
        p = self.p
        op = p.comprar_pacote(i)
        if op is None:
            self.som("erro")
            self.avisar("Moedas insuficientes para esses giros.")
            return
        self.som("deposito")
        if op["saque"]:
            self.flutuar(f"-{formatar(op['saque'])} do caixa", 1100, 240, VERMELHO, 22)
        self.flutuar(f"+{op['bilhetes']} bilhete" + ("s" if op["bilhetes"] > 1 else ""), 215, 662, (255, 180, 70), 22)
        self.fase = "pronto"
        self.premio_led = 0
        self.destaques = []

    def passar_rodada(self):
        if self.estado != "jogo" or self.modal or self.fase != "pacote":
            return
        self.p.passar_rodada()
        self.fase = "fim_rodada"
        self.agendar(0.3, self.encerrar_rodada)

    def girar(self):
        if self.estado != "jogo" or self.modal or self.fase != "pronto" or self.p.giros <= 0:
            return
        p = self.p
        g = p.sortear_giro()
        self.giro = g
        self.destaques = []
        self.premio_led = 0
        self.texto_grande = None
        self.fase = "girando"
        self.alavanca_t = 0.0
        pesos = [p.mods.peso(s) for s in SIMBOLOS]
        suspense = 0.0
        if not g.diabo:
            for r in range(LINHAS):
                if representante(g.grade[r][:4], p.mods.coringa, p.mods.equiv) is not None:
                    suspense = 0.7
        for c, rolo in enumerate(self.rolos):
            fita = random.choices(SIMBOLOS, pesos, k=24)
            finais = [g.grade[r][c] for r in range(LINHAS)]
            parar = 0.45 + c * 0.2 + (suspense if c == COLUNAS - 1 else 0.0)
            rolo.girar(finais, parar, fita)
        self.suspense_tocado = suspense == 0.0
        self.som("alavanca")

    def atualizar_rolos(self, dt):
        girando = False
        for rolo in self.rolos:
            if rolo.atualizar(dt):
                self.som(f"para{rolo.col}", 0.8)
                self.tremor = max(self.tremor, 1.5)
            if rolo.estado == "girando":
                girando = True
        if girando:
            self.timer_tick -= dt
            if self.timer_tick <= 0:
                self.timer_tick = 0.055
                self.som("tick", 0.6)
            ultimo = self.rolos[-1]
            if (self.estado == "jogo" and not self.suspense_tocado and ultimo.estado == "girando"
                    and all(r.estado != "girando" for r in self.rolos[:-1])):
                self.suspense_tocado = True
                self.som("suspense")
        if self.estado == "jogo" and self.fase == "girando" and all(r.estado != "girando" for r in self.rolos):
            self.fase = "contando"
            self.agendar(0.18, self.apos_parar)

    def apos_parar(self):
        g = self.giro
        if g.diabo:
            self.som("diabo")
            self.tremor = 16
            self.flash_vermelho = 1.0
            if g.ganho_diabo:
                self.anunciar("666", f"O crânio sorriu: +{formatar(g.ganho_diabo)} moedas!", VERMELHO, 2.2)
            elif g.perda:
                self.anunciar("666", f"O DIABO LEVOU {formatar(g.perda)} MOEDAS DO SEU BOLSO!", VERMELHO, 2.2)
            else:
                self.anunciar("666", "O diabo riu... mas seu bolso estava vazio.", VERMELHO, 2.2)
            for c in (1, 2, 3):
                x = REEL_X + c * PASSO + CEL // 2
                self.faiscas(x, REEL_Y + PASSO + CEL // 2, (255, 60, 30), 18, 260, 0.8, 5)
            self.agendar(1.6, self.concluir_giro)
        elif g.padroes:
            t = 0.0
            n = len(g.padroes)
            for i in range(n):
                self.agendar(t, lambda i=i: self.revelar_padrao(i))
                t += 0.12 if n >= 12 else max(0.14, 0.42 - 0.03 * i)
            self.agendar(t + 0.2, self.mostrar_total)
            self.agendar(t + 0.75, self.concluir_giro)
        else:
            if g.consolo:
                self.flutuar(f"+{formatar(g.consolo)} (Gato Preto)", 640, REEL_Y + REEL_H // 2, CINZA, 22)
            self.agendar(0.3, self.concluir_giro)

    def centro_celula(self, r, c):
        return (REEL_X + c * PASSO + CEL // 2, REEL_Y + r * PASSO + CEL // 2)

    def revelar_padrao(self, i):
        g = self.giro
        p = self.p
        pd = g.padroes[i]
        v = g.premios[i]
        self.destaques.append((pd, self.tempo))
        self.premio_led += v
        self.som(f"ding{min(i, 11)}")
        xs = [self.centro_celula(r, c) for r, c in pd.celulas]
        cx = sum(x for x, _ in xs) / len(xs)
        cy = sum(y for _, y in xs) / len(xs)
        cor = PADROES[pd.tipo]["cor"]
        self.flutuar(f"+{formatar(v)}", cx, cy - 10, cor, 30 if v < 1000 else 34, 1.0, -60)
        self.faiscas(cx, cy, cor, 8, 180, 0.5, 3)
        if v >= 25 * custo_giro(p.prazo):
            self.tremor = max(self.tremor, 5)
        # amuletos que ajudaram dão um pulinho
        tags = {"valor:" + pd.simbolo, "padrao:" + pd.tipo, "global", "corrente"}
        simbs = [g.grade[r][c] for r, c in pd.celulas]
        if p.mods.coringa and p.mods.coringa in simbs:
            tags.add("coringa")
        if p.mods.equiv and len(set(simbs)) > 1:
            tags.add("equiv")
        for k, aid in enumerate(p.amuletos):
            if AMULETOS[aid]["tags"] & tags:
                self.pulsos[k] = 0.35

    def mostrar_total(self):
        g = self.giro
        p = self.p
        total = g.total
        div = max(1, p.divida)
        if any(pd.tipo == "jackpot" for pd in g.padroes):
            self.texto_grande = ["JACKPOT!!!", OURO, 0.0]
            self.som("jackpot")
            self.flash_branco = 0.6
            self.tremor = 18
        elif total >= div * 0.5:
            self.texto_grande = ["INCRÍVEL!!", ROXO, 0.0]
            self.som("grande")
            self.tremor = 12
        elif total >= div * 0.2:
            self.texto_grande = ["ÓTIMO!", CIANO, 0.0]
            self.som("grande", 0.8)
            self.tremor = 7
        elif total >= div * 0.08:
            self.texto_grande = ["BOM!", VERDE, 0.0]
        self.voar_moedas((640, 474), (110, 630), 3 + total // max(1, custo_giro(p.prazo) * 3))

    def concluir_giro(self):
        p = self.p
        g = self.giro
        p.aplicar_giro(g)
        if g.bilhetes:
            self.flutuar("+1 bilhete (Caça-Bilhetes)", 215, 662, (255, 180, 70), 20)
            self.pulsar_amuleto("ima")
        if g.consolo:
            self.pulsar_amuleto("gato")
        if g.diabo:
            if g.perda:
                self.flutuar(f"-{formatar(g.perda)}", 150, 625, VERMELHO, 30)
                self.pulsar_amuleto("terco")
            if g.ganho_diabo:
                self.flutuar(f"+{formatar(g.ganho_diabo)}", 150, 625, OURO, 30)
                self.pulsar_amuleto("cranio")
        if p.giros <= 0:
            self.fase = "fim_rodada"
            self.agendar(0.6, self.encerrar_rodada)
        else:
            self.fase = "pronto"

    def pulsar_amuleto(self, aid):
        if aid in self.p.amuletos:
            self.pulsos[self.p.amuletos.index(aid)] = 0.4

    def encerrar_rodada(self):
        p = self.p
        j = p.fim_rodada()
        if j:
            self.som("juros")
            self.flutuar(f"+{formatar(j)} de juros", 1102, 200, VERDE_TELA, 24, 1.6)
            sub = f"O caixa rendeu {porcento(p.juros_atual())}: +{formatar(j)} moedas"
        elif p.mods.sem_juros:
            sub = "O Contrato Sangrento não deixa o caixa render juros."
        else:
            sub = "Sem moedas no caixa, sem juros. Deposite!"
        self.anunciar(f"FIM DA RODADA {p.rodada}", sub, BRANCO, 1.8)
        if p.rodada < RODADAS:
            self.agendar(1.5, self.proxima_rodada)
        else:
            self.agendar(1.5, self.checar_prazo)

    def proxima_rodada(self):
        p = self.p
        p.rodada += 1
        p.nova_loja()
        self.fase = "pacote"
        self.destaques = []
        self.som("virar")

    def checar_prazo(self):
        p = self.p
        self.fase = "fim_prazo"
        if p.bolso > 0:
            self.voar_moedas((110, 630), (1100, 160), 6 + p.bolso // max(1, custo_giro(p.prazo) * 4))
            self.flutuar("O caixa recolheu seu bolso", 1100, 250, VERDE_TELA, 20, 1.6)
            self.som("deposito")
        self.agendar(0.9, self.resolver_prazo)

    def resolver_prazo(self):
        p = self.p
        divida = p.divida
        if p.checar_prazo():
            self.prazo_pago(0)
        else:
            falta = divida - p.caixa
            self.anunciar("A DÍVIDA NÃO FOI PAGA", f"Faltaram {formatar(falta)} moedas...", VERMELHO, 3.0)
            self.som("erro")
            self.tremor = 10
            self.agendar(2.4, self.cair)

    def pagar_agora(self):
        p = self.p
        if not self.pode_mexer() or self.fase == "telefone" or not p.pode_pagar_agora():
            self.som("erro")
            return
        bonus = p.pagar_agora()
        self.prazo_pago(bonus)

    def prazo_pago(self, bonus):
        p = self.p
        self.fase = "fim_prazo"
        self.som("pagar")
        self.voar_moedas((1100, 160), (1100, -40), 14, 0.9, 60, som=False)
        sub = f"Pagou antes: +{bonus} bilhetes de bônus!" if bonus else "Você sobreviveu... por enquanto."
        self.anunciar("DÍVIDA PAGA!", sub, VERDE, 2.4)
        if bonus:
            self.flutuar(f"+{bonus} bilhetes", 215, 662, (255, 180, 70), 24)
        if p.prazos_pagos == PRAZOS_PARA_VENCER and not p.venceu:
            p.venceu = True
            self.agendar(2.3, self.mostrar_vitoria)
        else:
            self.agendar(2.3, self.proximo_prazo)

    def proximo_prazo(self):
        p = self.p
        self.ofertas, self.ligacao_maldita = p.concluir_prazo()
        self.estado = "jogo"
        self.fase = "telefone"
        self.timer_toque = 0.6
        self.destaques = []
        extra = "  (MODO INFINITO)" if p.prazo > PRAZOS_PARA_VENCER else ""
        self.anunciar(f"PRAZO {p.prazo}{extra}", f"Nova dívida: {formatar(p.divida)} moedas  •  "
                      f"o banco te deu {formatar(p.ajuda_banco)} moedas para girar", VERMELHO, 3.2)
        self.flutuar(f"+{formatar(p.ajuda_banco)}", 150, 625, OURO, 28, 1.6)

    def atender(self):
        if self.estado != "jogo" or self.modal or self.fase != "telefone":
            return
        self.som("atender")
        self.modal = "ligacao"

    def escolher_oferta(self, i):
        p = self.p
        if self.modal != "ligacao":
            return
        if i is not None:
            if not 0 <= i < len(self.ofertas) or not oferta_valida(p, self.ofertas[i]):
                self.som("erro")
                return
            o = self.ofertas[i]
            aplicar_oferta(p, o)
            titulo = texto_oferta(p, o)[0]
            self.som("diabo" if self.ligacao_maldita else "compra", 0.7)
            self.avisar(f"Você aceitou: {titulo}", VERMELHO if self.ligacao_maldita else VERDE)
        else:
            self.som("atender")
        self.modal = None
        self.fase = "pacote"

    def mostrar_vitoria(self):
        self.estado = "vitoria"
        self.modal = None
        self.som("vitoria")
        self.recorde["vitorias"] += 1
        self.registrar_recorde(contar_partida=False)
        for _ in range(140):
            self.particulas.append(Particula(random.uniform(0, LARGURA), random.uniform(-200, 0),
                                             random.uniform(-40, 40), random.uniform(60, 200), random.uniform(2, 4),
                                             random.uniform(3, 6), random.choice([OURO, VERDE, CIANO, ROXO, VERMELHO]), 40))

    def continuar_infinito(self):
        self.estado = "jogo"
        self.particulas = []
        self.proximo_prazo()

    def cair(self):
        self.estado = "queda"
        self.modal = None
        self.t_queda = 0.0
        self.som("queda")
        self.registrar_recorde()

    def registrar_recorde(self, contar_partida=True):
        p = self.p
        r = self.recorde
        if contar_partida:
            r["partidas"] += 1
        if p.prazos_pagos > r["melhor_prazo"]:
            r["melhor_prazo"] = p.prazos_pagos
            self.novo_recorde = True
        if p.stats["maior_giro"] > r["maior_giro"]:
            r["maior_giro"] = p.stats["maior_giro"]
        salvar_recorde(r)

    # ---------- caixa e loja ----------
    def depositar(self, metade=False):
        p = self.p
        if not self.pode_mexer():
            return
        q = p.bolso // 2 if metade else p.bolso
        if q <= 0:
            self.som("erro")
            self.avisar("Seu bolso está vazio.")
            return
        p.depositar(q)
        self.som("deposito")
        self.voar_moedas((110, 630), (1100, 160), 3 + q // max(1, custo_giro(p.prazo) * 4), 0.6, 140)
        self.flutuar(f"+{formatar(q)}", 1100, 230, VERDE_TELA, 24)

    def comprar(self, i):
        p = self.p
        if not self.pode_mexer():
            return
        a = p.loja[i] if i < len(p.loja) else None
        if a is None:
            return
        if len(p.amuletos) >= p.espacos:
            self.som("erro")
            self.avisar("Sem espaço! Venda um amuleto com o botão direito.")
            return
        if p.bilhetes < p.preco(a):
            self.som("erro")
            self.avisar("Bilhetes insuficientes.")
            return
        p.comprar(i)
        self.som("compra")
        r = pos_amuleto(len(p.amuletos) - 1)
        self.faiscas(r.centerx, r.centery, RARIDADES[AMULETOS[a]["rar"]]["cor"], 16, 200, 0.6, 4)
        self.pulsos[len(p.amuletos) - 1] = 0.4
        self.avisar(f"Comprou: {AMULETOS[a]['nome']}", VERDE)

    def vender(self, idx):
        p = self.p
        if not self.pode_mexer() or idx >= len(p.amuletos):
            return
        nome = AMULETOS[p.amuletos[idx]]["nome"]
        v = p.vender(idx)
        self.pulsos = {}
        self.som("virar")
        self.avisar(f"Vendeu {nome} por {v} bilhete" + ("s" if v > 1 else ""), LARANJA)

    def trocar_loja(self):
        p = self.p
        if not self.pode_mexer():
            return
        if not p.trocar_loja():
            self.som("erro")
            self.avisar("Bilhetes insuficientes para trocar a loja.")
            return
        self.som("virar")

    # -----------------------------------------------------------------
    # Atualização
    # -----------------------------------------------------------------
    def atualizar(self, dt):
        self.tempo += dt
        dtj = dt * self.velocidade
        self.mouse = self.para_logico(pygame.mouse.get_pos())

        # luz da lâmpada piscando
        self.timer_piscar -= dt
        if self.timer_piscar <= 0:
            self.piscando = random.uniform(0.25, 0.7)
            self.timer_piscar = random.uniform(6, 14)
        if self.piscando > 0:
            self.piscando -= dt
            self.luz = random.choice((0.25, 0.45, 1.0, 0.6))
        else:
            self.luz = 0.93 + 0.07 * math.sin(self.tempo * 13) * math.sin(self.tempo * 3.1)

        if self.estado == "menu":
            self.timer_demo -= dt
            if self.timer_demo <= 0 and all(r.estado == "parado" for r in self.rolos):
                self.timer_demo = 3.2
                for c, rolo in enumerate(self.rolos):
                    rolo.girar([random.choice(SIMBOLOS) for _ in range(LINHAS)], 0.4 + c * 0.15,
                               random.choices(SIMBOLOS, k=24))
            for rolo in self.rolos:
                rolo.atualizar(dt)
        elif self.estado == "jogo":
            if self.modal is None:
                self.atualizar_agenda(dtj)
                self.atualizar_rolos(dtj)
                if self.fase == "pronto" and pygame.key.get_pressed()[pygame.K_SPACE]:
                    self.girar()
                if self.fase == "telefone":
                    self.timer_toque -= dt
                    if self.timer_toque <= 0:
                        self.timer_toque = 2.3
                        self.som("telefone", 0.8)
            if self.alavanca_t >= 0:
                self.alavanca_t += dtj
                self.alavanca = suave(self.alavanca_t / 0.12) if self.alavanca_t < 0.12 else 1 - suave((self.alavanca_t - 0.12) / 0.35)
                if self.alavanca_t > 0.47:
                    self.alavanca_t = -1.0
                    self.alavanca = 0.0
            p = self.p
            for chave, alvo in (("bolso", p.bolso), ("caixa", p.caixa), ("bilhetes", p.bilhetes)):
                atual = self.contagem[chave]
                d = alvo - atual
                if abs(d) < 0.5:
                    self.contagem[chave] = float(alvo)
                else:
                    self.contagem[chave] = atual + d * min(1.0, dt * 7) + math.copysign(min(abs(d), 2.0), d) * dt * 10
        elif self.estado == "queda":
            self.t_queda += dt
            if self.t_queda >= 2.8:
                self.estado = "fim"
                self.t_fim = 0.0
        elif self.estado == "fim":
            self.t_fim += dt

        # efeitos
        for f in self.flutuantes:
            f.vida -= dt
            f.y += f.vy * dt
            f.vy *= max(0.0, 1 - 2.5 * dt)
        self.flutuantes = [f for f in self.flutuantes if f.vida > 0]
        for pt in self.particulas:
            pt.vida -= dt
            pt.vy += pt.gravidade * dt
            pt.x += pt.vx * dt
            pt.y += pt.vy * dt
        self.particulas = [pt for pt in self.particulas if pt.vida > 0 and pt.y < ALTURA + 50]
        restantes = []
        for v in self.voos:
            if v.atraso > 0:
                v.atraso -= dt
                restantes.append(v)
                continue
            v.t += dt
            if v.t >= v.dur:
                if v.som:
                    self.som("moeda", 0.5, intervalo=0.04)
            else:
                restantes.append(v)
        self.voos = restantes
        for k in list(self.pulsos):
            self.pulsos[k] -= dt
            if self.pulsos[k] <= 0:
                del self.pulsos[k]
        if self.anuncio:
            self.anuncio["t"] -= dt
            if self.anuncio["t"] <= 0:
                self.anuncio = None
        if self.aviso_txt:
            txt, cor, t = self.aviso_txt
            self.aviso_txt = (txt, cor, t - dt) if t - dt > 0 else None
        if self.texto_grande:
            self.texto_grande[2] += dt
            if self.texto_grande[2] > 1.6:
                self.texto_grande = None
        self.tremor = max(0.0, self.tremor - dt * 30)
        self.flash_vermelho = max(0.0, self.flash_vermelho - dt * 0.8)
        self.flash_branco = max(0.0, self.flash_branco - dt * 1.5)
        if random.random() < dt * 3:
            self.particulas.append(Particula(random.uniform(380, 900), random.uniform(60, 420), random.uniform(-6, 6),
                                             random.uniform(-4, 8), random.uniform(3, 6), random.uniform(1, 2.2),
                                             (120, 110, 90), 0, True))

    # -----------------------------------------------------------------
    # Desenho
    # -----------------------------------------------------------------
    def desenhar(self):
        self.botoes = []
        self.dicas = []
        self.direito = []
        e = self.estado
        if e == "menu":
            self.desenhar_menu()
        elif e in ("jogo", "queda"):
            self.desenhar_jogo()
        elif e == "vitoria":
            self.desenhar_jogo(interativo=False)
            self.desenhar_vitoria()
        elif e == "fim":
            self.desenhar_fim()
        if self.modal:
            self.botoes = []
            self.dicas = []
            self.direito = []
            if self.modal == "ligacao":
                self.desenhar_ligacao()
            elif self.modal == "tabela":
                self.desenhar_tabela()
            elif self.modal == "pausa":
                self.desenhar_pausa()
            elif self.modal == "ajuda":
                self.desenhar_ajuda()
        else:
            self.desenhar_dica()

        # apresenta na janela (com tremida ou queda)
        self.tela.fill(PRETO)
        if e == "queda":
            self.desenhar_queda()
        else:
            tr = min(self.tremor, 20) * self.k
            ox, oy = (random.uniform(-tr, tr), random.uniform(-tr, tr)) if tr > 0 else (0, 0)
            self.tela.blit(self.cena, (self.ox + int(ox), self.oy + int(oy)))

    def desenhar_cenario(self, texto_letreiro=True):
        """Parede, máquina, rolos e alavanca (usado no jogo e no menu)."""
        self.cena.blit(self.fundo, (0, 0))
        self.desenhar_letreiro(texto_letreiro)
        self.desenhar_rolos()
        self.desenhar_alavanca()

    def desenhar_letreiro(self, com_texto=True):
        lx, ly, lw, lh = R_LETREIRO
        n = 26
        per = 2 * (lw + lh)
        for i in range(n):
            d = i / n * per
            if d < lw:
                x, y = lx + d, ly
            elif d < lw + lh:
                x, y = lx + lw, ly + d - lw
            elif d < 2 * lw + lh:
                x, y = lx + lw - (d - lw - lh), ly + lh
            else:
                x, y = lx, ly + lh - (d - 2 * lw - lh)
            aceso = (i + int(self.tempo * 8)) % 3 == 0
            if aceso:
                self.brilhar((120, 90, 20), (x, y), 9)
            self.circulo((255, 230, 120) if aceso else (90, 60, 20), (x, y), 3)
        if not com_texto:
            return
        chave = "letreiro"
        g = self._sprites.get(chave)
        if g is None:
            rr = self.ret((lx + 20, ly, lw - 40, lh))
            g = pygame.transform.smoothscale(brilho((140, 30, 20), 70 * self.k), rr.size)
            self._sprites[chave] = g
        self.blit(g, (lx + 20, ly), flags=pygame.BLEND_ADD)
        self.escrever("SORTE OU MORTE", 38, (255, 70, 60), (lx + lw / 2, ly + lh / 2 + 1), tipo="titulo", negrito=False, sombra=3)

    def desenhar_rolos(self):
        t = self.cena
        t.set_clip(self.ret((REEL_X, REEL_Y, REEL_W, REEL_H)))
        for rolo in self.rolos:
            x = REEL_X + rolo.col * PASSO
            if rolo.estado == "girando":
                i0 = int(rolo.desloc // PASSO)
                frac = rolo.desloc % PASSO
                L = len(rolo.fita)
                imgs = self.img_borrada if rolo.vel > 1200 else self.img
                for kk in range(-1, LINHAS):
                    self.blit(imgs[rolo.fita[(i0 - kk) % L]], (x, REEL_Y + kk * PASSO + frac))
            else:
                off = rolo.deslocamento()
                for r in range(LINHAS):
                    self.blit(self.img[rolo.simbolos[r]], (x, REEL_Y + r * PASSO + off))
                if off < 0:
                    self.blit(self.img[rolo.fita[0]], (x, REEL_Y + LINHAS * PASSO + off))
        t.set_clip(None)
        for rolo in self.rolos:
            self.blit(self.sombra_rolo, (REEL_X + rolo.col * PASSO, REEL_Y))
        # destaques dos padrões
        if self.estado == "jogo":
            for idx, (pd, t0) in enumerate(self.destaques):
                cor = PADROES[pd.tipo]["cor"]
                idade = self.tempo - t0
                atual = idx == len(self.destaques) - 1 and self.fase == "contando"
                larg = 5 if atual else 3
                if atual:
                    cor_l = misturar(cor, BRANCO, _nivel(0.5 + 0.5 * math.sin(idade * 18)) * 0.6)
                else:
                    cor_l = escurecer(cor, 0.85)
                for r, c in pd.celulas:
                    if atual:
                        self.brilhar(escurecer(cor, 0.5), self.centro_celula(r, c), 48)
                    self.caixa((REEL_X + c * PASSO - 2, REEL_Y + r * PASSO - 2, CEL + 4, CEL + 4), cor_l, 10, cor_l, larg,
                               alpha=0, alpha_borda=255)
                if atual and pd.tipo not in ("jackpot", "olho"):
                    pts = [self.centro_celula(r, c) for r, c in pd.celulas]
                    if pd.tipo in ("v", "v_inv"):
                        pts.sort()
                    self.linhas(cor_l, pts, 6)
            g = self.giro
            if g is not None and g.diabo and self.fase in ("contando", "fim_rodada", "pronto"):
                pulso = _nivel(0.5 + 0.5 * math.sin(self.tempo * 10))
                for c in (1, 2, 3):
                    centro = self.centro_celula(1, c)
                    self.brilhar((int(160 + 90 * pulso), 20, 10), centro, 60)
                    self.blit(self.img["seis"], centro, "center")

    def desenhar_alavanca(self):
        px, py = PIVO_ALAVANCA
        ang = math.radians(-75 + 135 * self.alavanca)
        comp = 120
        bx, by = px + math.cos(ang) * comp * 0.25, py + math.sin(ang) * comp
        self.linha((80, 80, 90), (px, py), (bx, by), 12)
        self.linha((190, 190, 200), (px, py), (bx, by), 6)
        self.circulo((120, 10, 20), (bx, by), 19)
        self.circulo((225, 40, 50), (bx, by), 16)
        self.circulo((255, 160, 160), (bx - 5, by - 5), 5)
        self.circulo((60, 60, 70), (px, py), 9)
        self.pos_alavanca = pygame.Rect(int(bx) - 22, int(by) - 22, 44, 44)

    def desenhar_luz(self):
        # lâmpada pendurada
        self.linha((20, 20, 20), (640, 0), (640, 26), 3)
        self.caixa((633, 22, 14, 8), (60, 60, 60), 2)
        nivel = round(self.luz * 10) / 10
        self.circulo(misturar((80, 70, 40), (255, 240, 180), nivel), (640, 38), 11)
        self.brilhar(escurecer((150, 130, 80), nivel), (640, 38), 300)
        self.brilhar(escurecer((255, 230, 160), nivel), (640, 38), 26)
        # poeira no ar
        for pt in self.particulas:
            if pt.gravidade == 0 and pt.brilha and pt.tam < 2.5:
                a = min(1.0, pt.vida / pt.total * 3, (pt.total - pt.vida) * 2)
                if a > 0:
                    self.circulo(misturar((20, 18, 16), pt.cor, a), (pt.x, pt.y), pt.tam)
        self.cena.blit(self.vinheta, (0, 0))
        escuro = int((1 - self.luz) * 170)
        if escuro > 0:
            self.sup_escura.set_alpha(escuro)
            self.cena.blit(self.sup_escura, (0, 0))
        if self.flash_vermelho > 0:
            self.sup_vermelha.set_alpha(int(self.flash_vermelho * 120))
            self.cena.blit(self.sup_vermelha, (0, 0))
        if self.flash_branco > 0:
            self.sup_branca.set_alpha(int(self.flash_branco * 200))
            self.cena.blit(self.sup_branca, (0, 0))

    def desenhar_jogo(self, interativo=True):
        p = self.p
        self.desenhar_cenario()

        # telas de LED e botão de girar
        self.escrever(f"GIROS {p.giros}", 24, (255, 70, 60), (R_LED_GIROS[0] + R_LED_GIROS[2] / 2, R_LED_GIROS[1] + 22), tipo="mono", sombra=0)
        premio = f"+{formatar(self.premio_led)}" if self.premio_led else "-"
        self.escrever(premio, 24, (255, 215, 80), (R_LED_PREMIO[0] + R_LED_PREMIO[2] / 2, R_LED_PREMIO[1] + 22), tipo="mono", sombra=0)
        pode_girar = interativo and self.fase == "pronto" and p.giros > 0 and self.modal is None
        self.botao(R_GIRAR, "GIRAR", self.girar, pode_girar, (190, 30, 40), tam=22, destaque=pode_girar,
                   dica=("Girar", "Aperte ESPAÇO para girar. Segure para girar sem parar.", BRANCO))
        if pode_girar:
            self.botoes.append((self.pos_alavanca, self.girar, True))
        dica_maq = {"pacote": "Escolha os giros da rodada [1] ou [2]", "pronto": "ESPAÇO: girar  •  segure para girar sem parar",
                    "telefone": "O telefone está tocando! Atenda [T]"}.get(self.fase, "")
        self.escrever(dica_maq, 15, (220, 190, 170), (640, 515), sombra=1, negrito=False)

        if interativo:
            if self.fase == "pacote":
                self.desenhar_pacotes()
            elif self.fase == "telefone":
                self.desenhar_aviso_telefone()

        self.desenhar_telefone()
        self.desenhar_quadro()
        self.desenhar_caixa(interativo)
        self.desenhar_loja(interativo)
        self.desenhar_hud(interativo)
        self.desenhar_topo()

        # efeitos por cima
        for v in self.voos:
            if v.atraso > 0:
                continue
            q = suave(v.t / v.dur)
            x = v.a[0] + (v.b[0] - v.a[0]) * q
            y = v.a[1] + (v.b[1] - v.a[1]) * q - math.sin(q * math.pi) * v.altura
            self.moeda(x, y, 7)
        for pt in self.particulas:
            if pt.gravidade == 0 and pt.brilha and pt.tam < 2.5:
                continue
            r = pt.tam * (pt.vida / pt.total if pt.gravidade else 1)
            if pt.brilha:
                self.brilhar(escurecer(pt.cor, 0.6), (pt.x, pt.y), r * 2.5 + 2)
            if r >= 0.8:
                self.circulo(pt.cor, (pt.x, pt.y), r)
        for f in self.flutuantes:
            f.sup.set_alpha(int(255 * min(1.0, f.vida / 0.35)))
            self.blit(f.sup, (f.x, f.y), "center")

        self.desenhar_luz()
        if self.texto_grande:
            txt, cor, idade = self.texto_grande
            chave = ("grande", txt)
            base = self._sprites.get(chave)
            if base is None:
                base = self.texto_sombra(txt, 115, cor, "titulo")
                self._sprites[chave] = base
            esc = (1.0 + 0.6 * max(0.0, 0.25 - idade) / 0.25) / 1.6
            img = pygame.transform.smoothscale(base, (max(1, int(base.get_width() * esc)), max(1, int(base.get_height() * esc))))
            img.set_alpha(max(0, 255 if idade < 1.2 else int(255 * (1.6 - idade) / 0.4)))
            self.blit(img, (640, REEL_Y + REEL_H // 2), "center")
        self.desenhar_anuncio()
        if self.aviso_txt:
            txt, cor, _ = self.aviso_txt
            self.escrever(txt, 18, cor, (640, 568), sombra=2)

    def desenhar_pacotes(self):
        p = self.p
        self.caixa((REEL_X, REEL_Y, REEL_W, REEL_H), (14, 10, 12), 6, alpha=215)
        self.escrever(f"RODADA {p.rodada} DE {RODADAS} — ESCOLHA SEUS GIROS", 19, OURO, (640, REEL_Y + 22))
        ops = p.opcoes_pacote()
        for i, op in enumerate(ops):
            r = pygame.Rect(REEL_X + 14 + i * 230, REEL_Y + 44, 214, 168)
            linhas = f"{op['giros']} GIROS\n+{op['bilhetes']} bilhete" + ("s" if op["bilhetes"] > 1 else "")
            linhas += f"\ncusta {formatar(op['custo'])} moedas"
            if op["saque"] and op["pode"]:
                linhas += f"\nsaca {formatar(op['saque'])} do caixa"
            elif not op["pode"]:
                linhas += "\nsem dinheiro"
            cor = (40, 110, 60) if i == 0 else (40, 80, 140)
            self.botao(r, linhas, lambda i=i: self.escolher_pacote(i), op["pode"], cor, tam=24,
                       dica=(op["nome"], "Mais giros = mais chances de ganhar moedas." if i == 0
                             else "Menos giros, mas mais bilhetes para a loja de amuletos.", BRANCO))
            self.escrever(f"[{i + 1}]", 14, CINZA, (r.right - 18, r.top + 14), sombra=0)
        if not any(op["pode"] for op in ops):
            self.botao((REEL_X + 136, REEL_Y + 222, 200, 44), "PASSAR A RODADA", self.passar_rodada, True, (110, 40, 40), tam=18)
        else:
            self.escrever("Saques do caixa têm taxa de 10%", 14, (190, 170, 160), (640, REEL_Y + 238), sombra=1, negrito=False)

    def desenhar_aviso_telefone(self):
        self.caixa((REEL_X, REEL_Y, REEL_W, REEL_H), (14, 10, 12), 6, alpha=190)
        pisca = int(self.tempo * 3) % 2 == 0
        self.escrever("O TELEFONE ESTÁ TOCANDO", 26, OURO if pisca else BRANCO, (640, REEL_Y + 100))
        self.botao((REEL_X + 136, REEL_Y + 140, 200, 50), "ATENDER [T]", self.atender, True, (40, 110, 60), tam=20, destaque=True)

    def desenhar_telefone(self):
        tocando = self.estado == "jogo" and self.fase == "telefone" and self.modal is None
        dx = dy = 0
        if tocando and self.timer_toque > 1.2:
            dx = random.uniform(-3, 3)
            dy = random.uniform(-4, 1)
        # fio enrolado e fone
        self.linha((30, 5, 8), (250 + dx, 104 + dy), (262, 140), 4)
        for kk in range(8):
            self.circulo((60, 10, 14), (262 + (4 if kk % 2 else -4), 140 + kk * 10), 4, 2)
        corpo = (80 + dx, 82 + dy, 180, 26)
        self.caixa(corpo, (95, 12, 18), 12)
        for ex in (corpo[0] + 12, corpo[0] + corpo[2] - 12):
            self.circulo((70, 8, 12), (ex, corpo[1] + 19), 17)
            self.circulo((120, 18, 26), (ex, corpo[1] + 19), 12)
        self.caixa((corpo[0] + 15, corpo[1] + 5, 150, 10), (150, 30, 40), 4)
        r = pygame.Rect(R_TELEFONE)
        if tocando:
            if self.timer_toque > 1.2:
                self.escrever("TRIM!", 26, OURO, (r.centerx + random.uniform(-3, 3), r.top - 2), tipo="titulo", negrito=False)
            self.botoes.append((r, self.atender, True))
            self.brilhar((90, 70, 20), r.center, 140)
        self.dicas.append((r, ("Telefone", "Toca no começo de cada prazo com ofertas. Depois de um 666, quem liga é o diabo...", BRANCO)))

    def desenhar_quadro(self):
        p = self.p
        m = p.mods
        x0 = R_QUADRO[0] + 24
        y = R_QUADRO[1] + 30
        self.escrever("Anotações", 22, GIZ, (R_QUADRO[0] + R_QUADRO[2] / 2, y), tipo="giz", negrito=False, sombra=0)
        y += 34
        g_muitos = max(1, PACOTES[0][1] + m.giros_extra)
        g_poucos = max(1, PACOTES[1][1] + m.giros_extra)
        itens = [
            (f"Sorte: {m.sorte}", "Sorte", "Cada ponto aumenta a chance de um símbolo repetir o vizinho, formando mais padrões."),
            (f"666: {porcento(p.chance_666())} por giro", "666", "Chance de o diabo aparecer num giro e levar o seu BOLSO. O caixa fica seguro."),
            (f"Juros: {porcento(p.juros_atual())} por rodada", "Juros", "No fim de cada rodada, o caixa rende essa porcentagem do que tem guardado."),
            (f"Prêmios: {vezes(m.mult_global)}", "Bônus geral", "Multiplica todos os prêmios dos padrões."),
            (f"Giros: {g_muitos} ou {g_poucos}", "Giros por rodada", "Quantos giros cada opção dá no começo da rodada."),
            (f"Custo do giro: {formatar(math.ceil(p.custo_do_giro()))}", "Custo", "Cada giro custa isso em moedas, pago do bolso."),
        ]
        for txt, titulo, desc in itens:
            r = self.escrever(txt, 18, GIZ, (x0, y), ancora="midleft", tipo="giz", negrito=False, sombra=0)
            self.dicas.append((r.inflate(10, 6), (titulo, desc, BRANCO)))
            y += 30
        # risquinhos: dívidas pagas
        n = p.prazos_pagos
        bx, by = R_QUADRO[0] + 26, R_QUADRO[1] + R_QUADRO[3] - 74
        for k in range(n):
            g, i = divmod(k, 5)
            gx = bx + g * 44
            if i < 4:
                self.linha(GIZ, (gx + i * 8, by), (gx + i * 8 + 2, by + 22), 3)
            else:
                self.linha(GIZ, (gx - 4, by + 18), (gx + 30, by + 4), 3)
        if n:
            self.dicas.append((pygame.Rect(bx - 6, by - 4, 200, 30), ("Riscos", f"Você já pagou {n} dívida(s).", BRANCO)))
        self.botao((R_QUADRO[0] + 18, R_QUADRO[1] + R_QUADRO[3] - 44, R_QUADRO[2] - 36, 30), "TABELA DE PRÊMIOS [TAB]",
                   self.abrir_tabela, self.modal is None, (50, 72, 60), tam=15)

    def desenhar_caixa(self, interativo):
        p = self.p
        x, y, w, h = R_CAIXA
        self.escrever("BANCO DO POÇO  •  24H", 16, BRANCO, (x + w / 2, y + 21), sombra=1)
        tx, ty, tw, th = R_TELA_CAIXA
        verde = VERDE_TELA
        divida = p.divida
        saldo = int(round(self.contagem["caixa"]))
        linhas = [("SALDO", formatar(saldo), verde), ("DÍVIDA", formatar(divida), (255, 120, 100))]
        falta = divida - p.caixa
        if falta > 0:
            linhas.append(("FALTAM", formatar(falta), (255, 200, 90)))
        else:
            linhas.append(("PODE PAGAR!", "", (255, 255, 160) if int(self.tempo * 3) % 2 == 0 else verde))
        linhas.append(("JUROS", f"{porcento(p.juros_atual())}/rodada", verde))
        for i, (rot, val, cor) in enumerate(linhas):
            yy = ty + 16 + i * 26
            self.escrever(rot, 19, cor, (tx + 12, yy), ancora="midleft", tipo="mono", sombra=0)
            if val:
                self.escrever(val, 19, cor, (tx + tw - 12, yy), ancora="midright", tipo="mono", sombra=0)
        self.blit(self.linhas_caixa, (tx, ty))
        self.dicas.append((pygame.Rect(R_TELA_CAIXA), ("Caixa eletrônico", "Moedas no caixa ficam seguras do 666 e rendem juros "
                                                        "no fim de cada rodada. A dívida é paga com o saldo do caixa.", BRANCO)))
        livre = interativo and self.pode_mexer()
        self.botao((962, 232, 136, 40), "DEPOSITAR\nTUDO [D]", self.depositar, livre and p.bolso > 0, (40, 100, 60), tam=15)
        self.botao((1106, 232, 136, 40), "DEPOSITAR\nMETADE", lambda: self.depositar(True), livre and p.bolso > 1, (40, 80, 70), tam=15)
        pode_pagar = livre and self.fase != "telefone" and p.pode_pagar_agora()
        puladas = RODADAS - p.rodada + (0 if p.rodada_iniciada else 1)
        txt = "PAGAR DÍVIDA [P]"
        if pode_pagar and puladas > 0:
            txt += f"\n+{BONUS_ANTECIPADO * puladas} bilhetes por pagar antes"
        self.botao((962, 280, 280, 44), txt, self.pagar_agora, pode_pagar, (150, 110, 20), tam=17, destaque=pode_pagar,
                   dica=("Pagar dívida", "Paga a dívida agora com o saldo do caixa. Cada rodada que sobrar vale "
                         f"{BONUS_ANTECIPADO} bilhetes de bônus (mas você perde os giros restantes).", BRANCO))

    def desenhar_loja(self, interativo):
        p = self.p
        x, y, w, h = R_LOJA
        self.escrever("LOJA DE AMULETOS", 18, OURO, (x + 14, y + 20), ancora="midleft")
        livre = interativo and self.pode_mexer()
        self.botao((x + w - 110, y + 8, 98, 26), f"TROCAR [R]  {p.custo_troca}", self.trocar_loja, livre and p.bilhetes >= p.custo_troca,
                   (70, 60, 50), tam=13,
                   dica=("Trocar", f"Troca os 3 amuletos da loja por {p.custo_troca} bilhete(s). O preço sobe a cada troca no mesmo prazo.", BRANCO))
        for i in range(3):
            card = pygame.Rect(x + 12 + i * 100, y + 44, 92, 128)
            a = p.loja[i] if i < len(p.loja) else None
            if a is None:
                self.caixa(card, (30, 22, 18), 10, (70, 55, 40), 2)
                self.escrever("VENDIDO", 14, (110, 95, 80), card.center, sombra=0)
                continue
            info = AMULETOS[a]
            rar = RARIDADES[info["rar"]]
            preco = p.preco(a)
            hover = card.collidepoint(self.mouse) and livre
            self.caixa(card, (58, 44, 36) if hover else (42, 32, 26), 10, rar["cor"] if hover else escurecer(rar["cor"], 0.7), 2)
            self.blit(self.icone_amuleto(a, 56), (card.centerx, card.top + 38 - (3 if hover else 0)), "center")
            for kk, linha in enumerate(self.quebrar(info["nome"], 13, 84, negrito=True)[:2]):
                self.escrever(linha, 13, BRANCO, (card.centerx, card.top + 80 + kk * 15), sombra=1)
            pode = p.bilhetes >= preco
            self.bilhete(card.centerx - 14, card.bottom - 14, 22, 14)
            self.escrever(str(preco), 17, (255, 200, 90) if pode else (200, 90, 80), (card.centerx + 10, card.bottom - 14), sombra=1)
            self.botoes.append((card, lambda i=i: self.comprar(i), livre))
            self.dicas.append((card, (info["nome"], f"{rar['nome']} • {info['desc']}\nClique para comprar por {preco} bilhete(s).", rar["cor"])))

    def desenhar_hud(self, interativo):
        p = self.p
        # bolso e bilhetes
        bx, by, bw, bh = R_BOLSO
        self.escrever("BOLSO", 15, CINZA, (bx + 16, by + 16), ancora="midleft")
        self.moeda(bx + 30, by + 48, 13)
        self.escrever(formatar(round(self.contagem["bolso"])), 34, OURO, (bx + 52, by + 48), ancora="midleft")
        self.dicas.append((pygame.Rect(bx, by, bw, 68), ("Bolso", "Moedas que você ganhou. Cuidado: o 666 leva tudo que está no bolso! "
                                                       "Deposite no caixa.", OURO)))
        self.bilhete(bx + 30, by + 94, 28, 18)
        self.escrever(f"{int(round(self.contagem['bilhetes']))} bilhetes", 22, (255, 185, 80), (bx + 52, by + 94), ancora="midleft")
        self.dicas.append((pygame.Rect(bx, by + 72, bw, 46), ("Bilhetes", "Servem para comprar amuletos na loja.", (255, 185, 80))))
        # amuletos
        px_, py_, pw, ph = R_PRATELEIRA
        self.escrever(f"AMULETOS {len(p.amuletos)}/{p.espacos}", 14, CINZA, (px_ + 14, py_ - 6), ancora="midleft", sombra=1)
        self.escrever("botão direito: vender", 12, (120, 120, 130), (px_ + pw - 14, py_ - 6), ancora="midright", sombra=0, negrito=False)
        for i in range(MAX_ESPACOS):
            r = pos_amuleto(i)
            if i >= p.espacos:
                self.escrever("\U0001F512", 22, (70, 60, 50), r.center, tipo="simbolo", negrito=False, sombra=0)
                continue
            if i < len(p.amuletos):
                aid = p.amuletos[i]
                info = AMULETOS[aid]
                rar = RARIDADES[info["rar"]]
                pulso = self.pulsos.get(i, 0.0)
                tam = 68 + int(14 * math.sin(pulso / 0.4 * math.pi)) if pulso > 0 else 68
                if pulso > 0:
                    self.brilhar(escurecer(rar["cor"], 0.6), r.center, 60)
                if info["rar"] == "maldito":
                    self.brilhar((60 + int(40 * _nivel(0.5 + 0.5 * math.sin(self.tempo * 4))), 5, 5), r.center, 50)
                self.blit(self.icone_amuleto(aid, tam), r.center, "center")
                self.dicas.append((r, (info["nome"], f"{rar['nome']} • {info['desc']}\nBotão direito: vender por "
                                                     f"{p.valor_venda(aid)} bilhete(s).", rar["cor"])))
                if interativo:
                    self.direito.append((r, lambda i=i: self.vender(i)))
        # menu
        mx, my, mw, mh = R_MENU_HUD
        livre = interativo and self.modal is None
        self.botao((mx + 12, my + 10, mw - 24, 30), "TABELA DE PRÊMIOS [TAB]", self.abrir_tabela, livre, (55, 60, 75), tam=14)
        self.botao((mx + 12, my + 46, (mw - 30) // 2, 30), f"VELOCIDADE {self.velocidade}x", self.alternar_velocidade, livre, (55, 60, 75), tam=13)
        self.botao((mx + 18 + (mw - 30) // 2, my + 46, (mw - 30) // 2, 30), "SOM: " + ("NÃO" if self.sons.mudo else "SIM"),
                   self.alternar_som, livre, (55, 60, 75), tam=13)
        self.botao((mx + 12, my + 82, mw - 24, 30), "PAUSA [ESC]", lambda: self.abrir_modal("pausa"), livre, (75, 45, 50), tam=14)

    def desenhar_topo(self):
        p = self.p
        infinito = p.prazo > PRAZOS_PARA_VENCER
        txt = f"PRAZO {p.prazo}" + (" (INFINITO)" if infinito else f" DE {PRAZOS_PARA_VENCER}")
        self.escrever(txt, 30, OURO, (24, 30), ancora="midleft", tipo="titulo", negrito=False, sombra=3)
        self.escrever(f"Rodada {p.rodada} de {RODADAS}", 17, BRANCO, (26, 60), ancora="midleft", sombra=2)
        self.escrever(f"DÍVIDA: {formatar(p.divida)}", 30, (255, 90, 80), (LARGURA - 24, 30), ancora="midright", tipo="titulo", negrito=False, sombra=3)

    def desenhar_anuncio(self):
        a = self.anuncio
        if not a:
            return
        passado = a["dur"] - a["t"]
        alpha = 255
        if passado < 0.2:
            alpha = int(255 * passado / 0.2)
        elif a["t"] < 0.4:
            alpha = int(255 * a["t"] / 0.4)
        y = 98                          # no alto, para não cobrir a máquina
        self.faixa_anuncio.set_alpha(int(190 * alpha / 255))
        self.blit(self.faixa_anuncio, (0, y - 48))
        for txt, tam, cor, dy, tipo in ((a["texto"], 48, a["cor"], -12, "titulo"), (a["sub"], 20, BRANCO, 28, "ui")):
            if not txt:
                continue
            f = self.fonte(tam, tipo, tipo == "ui")
            s = f.render(txt, True, cor)
            sh = f.render(txt, True, PRETO)
            s.set_alpha(alpha)
            sh.set_alpha(alpha)
            self.blit(sh, (LARGURA / 2 + 3, y + dy + 3), "center")
            self.blit(s, (LARGURA / 2, y + dy), "center")

    def desenhar_dica(self):
        for r, (titulo, texto, cor) in reversed(self.dicas):
            if r.collidepoint(self.mouse):
                break
        else:
            return
        linhas = self.quebrar(texto, 15, 280)
        h = 40 + len(linhas) * 19
        x = min(self.mouse[0] + 16, LARGURA - 310)
        y = self.mouse[1] + 18
        if y + h > ALTURA - 6:
            y = self.mouse[1] - h - 10
        self.caixa((x, y, 300, h), (14, 14, 20), 12, cor, 2, alpha=235)
        self.escrever(titulo, 17, cor, (x + 12, y + 16), ancora="midleft", sombra=1)
        for i, linha in enumerate(linhas):
            self.escrever(linha, 15, (220, 222, 230), (x + 12, y + 38 + i * 19), ancora="midleft", sombra=0, negrito=False)

    # ---------- modais ----------
    def abrir_modal(self, nome):
        if self.estado == "jogo" and self.modal is None:
            self.modal = nome
            self.som("virar")

    def abrir_tabela(self):
        self.abrir_modal("tabela")

    def alternar_velocidade(self):
        self.velocidade = 2 if self.velocidade == 1 else 1

    def alternar_som(self):
        self.sons.mudo = not self.sons.mudo
        if self.sons.mudo:
            pygame.mixer.stop()
            self.sons.canal_ambiente = None
        else:
            self.sons.ambiente(True)

    def fechar_modal(self):
        self.modal = None

    def fundo_modal(self, alpha=170):
        self.sup_escura.set_alpha(alpha)
        self.cena.blit(self.sup_escura, (0, 0))

    def desenhar_ligacao(self):
        p = self.p
        mal = self.ligacao_maldita
        self.fundo_modal(190 if mal else 160)
        cor_borda = (200, 40, 40) if mal else (120, 140, 170)
        cor_fundo = (36, 6, 10) if mal else (16, 20, 30)
        self.caixa((170, 90, 940, 540), cor_fundo, 16, cor_borda, 2, alpha=245)
        if mal:
            self.brilhar((80 + int(30 * _nivel(0.5 + 0.5 * math.sin(self.tempo * 5))), 0, 0), (640, 160), 300)
        titulo = "UMA VOZ ROUCA DO OUTRO LADO..." if mal else "ALGUÉM LIGOU PARA VOCÊ"
        cor_t = (255, 80, 70) if mal else OURO
        r_t = self.escrever(titulo, 30, cor_t, (660, 134))
        self.escrever("☎", 34, cor_t, (r_t.left - 26, 134), tipo="simbolo", negrito=False)
        frases = (["— Eu vi o meu 666 na sua máquina... Vamos fazer um trato?", "— Toda sorte tem um preço. Escolha o seu."]
                  if mal else ["Uma voz cansada sussurra: — Ainda vivo? Pegue um presente.",
                               "— Não sei por que estou te ajudando... Escolha um."])
        self.escrever(frases[p.prazo % 2], 19, (230, 200, 200) if mal else (210, 215, 225), (640, 174), negrito=False, sombra=1)
        for i, o in enumerate(self.ofertas):
            card = pygame.Rect(200 + i * 300, 214, 280, 300)
            valida = oferta_valida(p, o)
            hover = valida and card.collidepoint(self.mouse)
            fundo = (60, 16, 20) if mal else (30, 38, 54)
            if hover:
                fundo = clarear(fundo, 0.12)
            self.caixa(card, fundo, 14, cor_borda if hover else escurecer(cor_borda, 0.7), 3 if hover else 2)
            titulo_o, desc, icone = texto_oferta(p, o)
            self.blit(self.icone_generico(icone, 72, (220, 70, 60) if mal else (120, 190, 255)), (card.centerx, card.top + 62), "center")
            for kk, linha in enumerate(self.quebrar(titulo_o, 22, 250, negrito=True)[:2]):
                self.escrever(linha, 22, BRANCO, (card.centerx, card.top + 124 + kk * 26))
            for kk, linha in enumerate(self.quebrar(desc, 17, 248)[:6]):
                self.escrever(linha, 17, (215, 215, 225), (card.centerx, card.top + 182 + kk * 22), negrito=False, sombra=1)
            self.escrever(f"[{i + 1}]" if valida else "SEM ESPAÇO", 16, CINZA if valida else VERMELHO, (card.centerx, card.bottom - 18), sombra=0)
            self.botoes.append((card, lambda i=i: self.escolher_oferta(i), valida))
        self.botao((560, 540, 160, 44), "DESLIGAR [ESC]", lambda: self.escolher_oferta(None), True, (80, 40, 40), tam=17)

    def desenhar_tabela(self):
        p = self.p
        m = p.mods
        self.fundo_modal(185)
        self.caixa((90, 40, 1100, 640), (16, 18, 26), 16, (110, 120, 145), 2, alpha=245)
        self.escrever("TABELA DE PRÊMIOS", 34, OURO, (640, 76), tipo="titulo", negrito=False)
        self.escrever("Prêmio = valor do símbolo × multiplicador do padrão × bônus. Vários padrões no mesmo giro somam!",
                      16, (200, 205, 215), (640, 108), negrito=False, sombra=1)
        # símbolos
        self.escrever("SÍMBOLOS", 20, CIANO, (130, 140), ancora="midleft")
        total_peso = sum(m.peso(s) for s in SIMBOLOS)
        for i, s in enumerate(SIMBOLOS):
            y = 172 + i * 62
            self.blit(self.img_media[s], (124, y - 4))
            info = INFO_SIMBOLO[s]
            nome = info["nome"]
            if m.coringa == s:
                nome += " (curinga)"
            if m.equiv.get(s):
                nome += f" (= {INFO_SIMBOLO[m.equiv[s]]['nome']})"
            self.escrever(nome, 20, BRANCO, (200, y + 14), ancora="midleft")
            val = m.valor(s)
            self.escrever(f"vale {formatar(val)}", 18, VERDE if val > info["valor"] else BRANCO, (200, y + 40), ancora="midleft", negrito=False)
            self.escrever(f"chance {porcento(m.peso(s) / total_peso)}", 18, (200, 200, 210), (360, y + 40), ancora="midleft", negrito=False)
        # padrões
        self.escrever("PADRÕES", 20, CIANO, (560, 140), ancora="midleft")
        for i, tipo in enumerate(ORDEM_PADROES):
            col, lin = divmod(i, 5)
            x = 560 + col * 300
            y = 166 + lin * 74
            info = PADROES[tipo]
            cel = EXEMPLO_PADRAO[tipo]
            for r in range(LINHAS):
                for c in range(COLUNAS):
                    self.caixa((x + c * 15, y + r * 15, 13, 13), info["cor"] if (r, c) in cel else (50, 54, 66), 3)
            mult = info["mult"] * m.padrao_mult[tipo]
            self.escrever(info["nome"], 19, info["cor"], (x + 86, y + 10), ancora="midleft")
            self.escrever(f"{vezes(mult)}  •  {info['desc']}", 14, (200, 205, 215), (x + 86, y + 34), ancora="midleft", negrito=False, sombra=0)
        notas = [f"Sorte {m.sorte}: cada casa tem {porcento(min(0.5, m.sorte * 0.03))} de chance de copiar um vizinho.",
                 f"Bônus geral dos prêmios: {vezes(m.mult_global)}" + ("  •  Corrente da Sorte: cada padrão vale +50% que o anterior" if m.corrente else ""),
                 f"666: {porcento(p.chance_666())} por giro — leva o bolso inteiro" + (" (o Terço salva metade)" if m.terco else "") + "."]
        for kk, nota in enumerate(notas):
            self.escrever(nota, 15, (190, 195, 210), (560, 550 + kk * 22), ancora="midleft", negrito=False, sombra=0)
        self.botao((560, 626, 160, 40), "FECHAR [TAB]", self.fechar_modal, True, (60, 64, 80), tam=17)

    def desenhar_pausa(self):
        self.fundo_modal(170)
        self.caixa((440, 180, 400, 340), (16, 16, 22), 16, (110, 110, 130), 2, alpha=245)
        self.escrever("PAUSADO", 46, BRANCO, (640, 230), tipo="titulo", negrito=False)
        self.botao((490, 280, 300, 48), "CONTINUAR [ESC]", self.fechar_modal, True, (40, 100, 60), tam=19)
        self.botao((490, 340, 300, 48), "COMO JOGAR", lambda: setattr(self, "modal", "ajuda"), True, (55, 60, 80), tam=19)
        self.botao((490, 400, 300, 48), "DESISTIR (VOLTAR AO MENU)", self.desistir, True, (110, 40, 40), tam=17)
        self.escrever("A partida fica parada enquanto o jogo está pausado.", 14, CINZA, (640, 485), negrito=False, sombra=0)

    def desistir(self):
        if self.p is not None and self.estado == "jogo":
            self.registrar_recorde()
        self.ir_menu()

    def ir_menu(self):
        self.limpar_efeitos()
        self.estado = "menu"
        self.modal = None

    def desenhar_ajuda(self):
        self.fundo_modal(200)
        self.caixa((110, 40, 1060, 640), (16, 16, 22), 16, (130, 120, 90), 2, alpha=248)
        self.escrever("COMO JOGAR", 40, OURO, (640, 82), tipo="titulo", negrito=False)
        topicos = [
            ("A DÍVIDA", "Você está preso. Para sair, pague a DÍVIDA no CAIXA antes do PRAZO acabar. Cada prazo tem 3 rodadas. "
                         "Pague 8 dívidas para ficar livre. Se não pagar... o chão se abre."),
            ("AS RODADAS", "No começo de cada rodada escolha MUITOS GIROS (7 giros e 1 bilhete) ou POUCOS GIROS (3 giros e "
                           "3 bilhetes). Os giros custam moedas do bolso."),
            ("A MÁQUINA", "Símbolos iguais em linha, coluna, diagonal, V ou formas especiais pagam prêmios. Vários padrões "
                          "no mesmo giro somam. Veja tudo na TABELA DE PRÊMIOS [TAB]."),
            ("BOLSO E CAIXA", "O que você ganha vai para o BOLSO. Deposite no CAIXA: lá fica seguro e rende juros no fim de "
                              "cada rodada. No fim do prazo, o caixa recolhe o bolso sozinho."),
            ("O 666", "Às vezes o diabo aparece na máquina e leva TODO o seu bolso. Depois disso, ele mesmo liga para você "
                      "oferecendo pactos poderosos... e perigosos."),
            ("AMULETOS E TELEFONE", "Use BILHETES na loja para comprar AMULETOS, que mudam as regras a seu favor (botão direito "
                                    "vende). No começo de cada prazo o telefone toca com um presente."),
            ("PAGAR ANTES", "Se o caixa já tem o valor da dívida, pague antes do fim: cada rodada que sobrar vale +3 bilhetes."),
        ]
        y = 124
        for titulo, texto in topicos:
            self.escrever(titulo, 19, CIANO, (150, y), ancora="midleft")
            linhas = self.quebrar(texto, 16, 960)
            for kk, linha in enumerate(linhas):
                self.escrever(linha, 16, (220, 222, 230), (150, y + 24 + kk * 20), ancora="midleft", negrito=False, sombra=0)
            y += 30 + len(linhas) * 20 + 8
        self.botao((560, 626, 160, 40), "VOLTAR", self.voltar_ajuda, True, (60, 64, 80), tam=18)

    def voltar_ajuda(self):
        self.modal = "pausa" if self.estado == "jogo" else None

    # ---------- telas ----------
    def desenhar_menu(self):
        self.desenhar_cenario(texto_letreiro=False)
        self.escrever("GIROS --", 24, (255, 70, 60), (R_LED_GIROS[0] + R_LED_GIROS[2] / 2, R_LED_GIROS[1] + 22), tipo="mono", sombra=0)
        self.desenhar_luz()
        self.fundo_modal(150)
        pisca = _nivel(0.85 + 0.15 * math.sin(self.tempo * 7), 6) if self.luz > 0.8 else 0.4
        self.brilhar((int(140 * pisca), 15, 10), (640, 150), 260)
        self.escrever("SORTE OU MORTE", 110, misturar((120, 20, 20), (255, 60, 50), pisca), (640, 150), tipo="titulo", negrito=False, sombra=6)
        self.escrever("Pague a dívida... ou caia no poço.", 26, (230, 220, 220), (640, 228), negrito=False)
        rec = self.recorde
        if rec["partidas"]:
            txt = f"Melhor: {rec['melhor_prazo']} dívida(s) paga(s)  •  Maior giro: {formatar(rec['maior_giro'])}"
            if rec["vitorias"]:
                txt += f"  •  Fugas: {rec['vitorias']}"
            self.escrever(txt, 18, CIANO, (640, 266), sombra=2)
        self.botao((490, 320, 300, 58), "JOGAR [ENTER]", self.nova_partida, True, (160, 30, 40), tam=24, destaque=True)
        self.botao((490, 392, 300, 50), "COMO JOGAR [H]", lambda: setattr(self, "modal", "ajuda"), True, (55, 60, 80), tam=20)
        self.botao((490, 456, 300, 50), "SAIR [ESC]", self.pedir_saida, True, (70, 45, 50), tam=20)
        self.escrever("F11: tela cheia  •  Inspirado no CloverPit  •  Só moedas de mentira: na vida real, a casa sempre ganha.",
                      15, (170, 165, 165), (640, 690), negrito=False, sombra=1)

    def pedir_saida(self):
        self.sair = True

    def desenhar_vitoria(self):
        self.fundo_modal(150)
        for pt in self.particulas:
            if pt.gravidade == 40:
                pygame.draw.rect(self.cena, pt.cor, self.ret((pt.x, pt.y, pt.tam, pt.tam * 1.6)))
        self.brilhar((140, 110, 30), (640, 170), 280)
        self.escrever("VOCÊ ESTÁ LIVRE!", 90, OURO, (640, 150), tipo="titulo", negrito=False, sombra=5)
        self.escrever("A porta da cela se abre. Você pagou as 8 dívidas.", 24, BRANCO, (640, 220))
        self.desenhar_estatisticas(262)
        self.botao((330, 600, 300, 54), "CONTINUAR (MODO INFINITO)", self.continuar_infinito, True, (110, 60, 140), tam=18)
        self.botao((650, 600, 300, 54), "VOLTAR AO MENU", self.ir_menu, True, (60, 64, 80), tam=18)

    def desenhar_estatisticas(self, y0):
        p = self.p
        st = p.stats
        dados = [("Dívidas pagas", str(p.prazos_pagos)), ("Giros feitos", formatar(st["giros"])),
                 ("Total ganho", formatar(st["ganho"])), ("Maior prêmio num giro", formatar(st["maior_giro"])),
                 ("Padrões formados", formatar(st["padroes"])), ("Vezes que saiu 666", str(st["diabos"]))]
        painel = pygame.Rect(390, y0, 500, 30 + len(dados) * 34 + 60)
        self.caixa(painel, (14, 14, 20), 12, (100, 100, 120), 2, alpha=220)
        for i, (nome, valor) in enumerate(dados):
            y = y0 + 30 + i * 34
            self.escrever(nome, 19, (205, 205, 215), (painel.x + 24, y), ancora="midleft", negrito=False, sombra=1)
            self.escrever(valor, 21, OURO if i == 0 else BRANCO, (painel.right - 24, y), ancora="midright", sombra=1)
        y = y0 + 30 + len(dados) * 34 + 10
        self.escrever("Amuletos:", 16, CINZA, (painel.x + 24, y), ancora="midleft")
        for kk, aid in enumerate(p.amuletos):
            self.blit(self.icone_amuleto(aid, 36), (painel.x + 110 + kk * 42, y - 18))

    def desenhar_queda(self):
        """O chão se abre e você cai."""
        W, H = self.cena.get_size()
        ox, oy = self.ox, self.oy
        tq = self.t_queda
        if tq < 0.7:
            tr = 10 * tq / 0.7 * self.k
            self.tela.blit(self.cena, (ox + random.uniform(-tr, tr), oy + random.uniform(-tr, tr)))
            h = int(260 * self.k * suave(tq / 0.7))
            pygame.draw.rect(self.tela, PRETO, (ox, oy + H - h, W, h))
            queda = int(math.sin(suave(tq / 0.7) * 1.2) * 120 * self.k)
            yb = oy + H - h
            for lado in (0, 1):
                x0 = ox if lado == 0 else ox + W
                pygame.draw.polygon(self.tela, (40, 36, 34), [(x0, yb), (ox + W // 2, yb), (ox + W // 2, yb + queda), (x0, yb + queda)])
        else:
            q = (tq - 0.7) / 1.6
            dy = -int(H * 1.4 * q * q)
            self.tela.blit(self.cena, (ox, oy + dy))
            pygame.draw.rect(self.tela, PRETO, (ox, oy + H + dy, W, H - dy + 10))
            self.sup_escura.set_alpha(int(255 * limitar(q, 0, 1)))
            self.tela.blit(self.sup_escura, (ox, oy))
        if tq > 1.6:
            a = int(255 * limitar((tq - 1.6) / 0.8, 0, 1))
            s = self.fonte(70, "titulo", False).render("VOCÊ CAIU NO POÇO", True, (200, 30, 30))
            s.set_alpha(a)
            self.tela.blit(s, s.get_rect(center=(ox + W // 2, oy + H // 2)))

    def desenhar_fim(self):
        self.cena.fill((6, 4, 6))
        self.brilhar((70, 8, 8), (640, 180), 300)
        self.escrever("VOCÊ CAIU NO POÇO", 80, (210, 35, 35), (640, 130), tipo="titulo", negrito=False, sombra=5)
        sub = "A dívida não foi paga a tempo." if self.p.prazos_pagos == 0 else f"Você pagou {self.p.prazos_pagos} dívida(s) antes de cair."
        self.escrever(sub, 24, (220, 210, 210), (640, 200))
        if self.novo_recorde and int(self.tempo * 3) % 2 == 0:
            self.escrever("NOVO RECORDE!", 28, OURO, (640, 245))
        self.desenhar_estatisticas(280)
        if self.t_fim > 0.6:
            self.botao((330, 580, 300, 54), "TENTAR DE NOVO [ENTER]", self.nova_partida, True, (160, 30, 40), tam=19, destaque=True)
            self.botao((650, 580, 300, 54), "MENU [ESC]", self.ir_menu, True, (60, 64, 80), tam=19)

    # -----------------------------------------------------------------
    # Entrada
    # -----------------------------------------------------------------
    def processar_evento(self, ev):
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_F11:
            self.alternar_tela_cheia()
            return
        if ev.type == pygame.KEYDOWN and ev.key == pygame.K_m:
            self.alternar_som()
            return
        if ev.type == pygame.MOUSEBUTTONDOWN:
            pos = self.para_logico(ev.pos)
            if ev.button == 1:
                for r, acao, ativo in reversed(self.botoes):
                    if r.collidepoint(pos):
                        if ativo:
                            acao()
                        else:
                            self.som("erro", 0.5)
                        return
            elif ev.button == 3:
                for r, acao in reversed(self.direito):
                    if r.collidepoint(pos):
                        acao()
                        return
            return
        if ev.type != pygame.KEYDOWN:
            return
        k = ev.key
        e = self.estado
        if self.modal:
            if self.modal == "ligacao":
                if pygame.K_1 <= k <= pygame.K_3:
                    self.escolher_oferta(k - pygame.K_1)
                elif k == pygame.K_ESCAPE:
                    self.escolher_oferta(None)
            elif self.modal == "tabela" and k in (pygame.K_TAB, pygame.K_ESCAPE):
                self.fechar_modal()
            elif self.modal == "pausa" and k == pygame.K_ESCAPE:
                self.fechar_modal()
            elif self.modal == "ajuda" and k in (pygame.K_ESCAPE, pygame.K_h):
                self.voltar_ajuda()
            return
        if e == "menu":
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER, pygame.K_SPACE):
                self.nova_partida()
            elif k == pygame.K_h:
                self.modal = "ajuda"
            elif k == pygame.K_ESCAPE:
                self.sair = True
        elif e == "jogo":
            if k == pygame.K_ESCAPE:
                self.abrir_modal("pausa")
            elif k == pygame.K_TAB:
                self.abrir_tabela()
            elif k == pygame.K_SPACE:
                self.girar()
            elif k in (pygame.K_1, pygame.K_2) and self.fase == "pacote":
                self.escolher_pacote(k - pygame.K_1)
            elif k == pygame.K_d:
                self.depositar()
            elif k == pygame.K_p:
                self.pagar_agora()
            elif k == pygame.K_t:
                self.atender()
            elif k == pygame.K_r:
                self.trocar_loja()
            elif k == pygame.K_f:
                self.alternar_velocidade()
        elif e == "fim" and self.t_fim > 0.6:
            if k in (pygame.K_RETURN, pygame.K_KP_ENTER):
                self.nova_partida()
            elif k == pygame.K_ESCAPE:
                self.ir_menu()
        elif e == "vitoria":
            if k == pygame.K_ESCAPE:
                self.ir_menu()

    # -----------------------------------------------------------------
    # Laço principal
    # -----------------------------------------------------------------
    def executar(self):
        while not self.sair:
            dt = min(self.relogio.tick(FPS) / 1000, 1 / 20)
            for ev in pygame.event.get():
                if ev.type == pygame.QUIT:
                    self.sair = True
                else:
                    self.processar_evento(ev)
            self.atualizar(dt)
            self.desenhar()
            pygame.display.flip()


def main():
    jogo = Jogo()
    jogo.executar()
    pygame.quit()


if __name__ == "__main__":
    main()
