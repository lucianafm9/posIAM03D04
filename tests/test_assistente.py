"""Testes sem modelo: base, busca, estrutura de contexto, gabarito e avaliação.
Uso: python -m unittest discover -s tests -v
"""

import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from assistente.avaliacao import avaliar, e_recusa, resumir  # noqa: E402
from assistente.base import carregar_base, texto_documento  # noqa: E402
from assistente.busca import buscar  # noqa: E402
from assistente.dataset import carregar_perguntas, exemplo_treino  # noqa: E402
from assistente.prompts import RECUSA, montar_mensagens  # noqa: E402
from assistente.texto import normalizar  # noqa: E402


class TestBase(unittest.TestCase):
    def test_oito_documentos_divididos_em_secoes(self):
        trechos = carregar_base()
        self.assertEqual(len({t.doc_id for t in trechos}), 8)
        self.assertTrue(all(t.texto and t.secao != "Objetivo" for t in trechos))


class TestBusca(unittest.TestCase):
    def test_pergunta_na_base_recupera_documento_certo_no_topo(self):
        trechos = buscar("Qual o free time para contêiner de importação?")
        self.assertEqual(trechos[0][0].doc_id, "POL-04")

    def test_busca_devolve_no_maximo_k(self):
        self.assertLessEqual(len(buscar("velocidade pátio", k=2)), 2)


class TestContexto(unittest.TestCase):
    def test_modo_sem_contexto_nao_leva_trechos(self):
        msgs = montar_mensagens("Qual a tolerância?")
        self.assertNotIn("CONTEXTO", msgs[1]["content"])

    def test_modo_com_contexto_leva_trechos_e_regra_de_recusa(self):
        trechos = [t for t, _ in buscar("tolerância de atraso do motorista")]
        msgs = montar_mensagens("Qual a tolerância?", trechos)
        self.assertIn(RECUSA, msgs[0]["content"])
        self.assertIn("[POL-01", msgs[1]["content"])
        self.assertIn("30 minutos", msgs[1]["content"])

    def test_exemplo_de_treino_no_formato_chat_da_aula(self):
        casos = {c["id"]: c for c in carregar_perguntas()}
        ex = exemplo_treino(casos["T01"])
        self.assertEqual([m["role"] for m in ex["messages"]], ["system", "user", "assistant"])
        self.assertTrue(ex["messages"][2]["content"].endswith("[Fonte: POL-01]"))
        self.assertEqual(exemplo_treino(casos["T31"])["messages"][2]["content"], RECUSA)


class TestGabarito(unittest.TestCase):
    def test_todo_fato_esperado_esta_no_documento_fonte(self):
        for c in carregar_perguntas():
            if c["fonte"] is None:
                continue
            doc = normalizar(texto_documento(c["fonte"]))
            for fato in c["fatos"]:
                with self.subTest(caso=c["id"], fato=fato):
                    self.assertTrue(any(normalizar(v) in doc for v in fato.split("|")))

    def test_treino_e_teste_nao_repetem_perguntas(self):
        perguntas = carregar_perguntas()
        treino = {c["pergunta"] for c in perguntas if c["split"] == "treino"}
        self.assertFalse(treino & {c["pergunta"] for c in perguntas if c["split"] == "teste"})


class TestAvaliacao(unittest.TestCase):
    caso_base = {"fonte": "POL-01", "fatos": ["30 minutos|meia hora"]}
    caso_fora = {"fonte": None, "fatos": []}

    def test_categorias(self):
        self.assertEqual(avaliar("Tolerância de meia hora. [Fonte: POL-01]", self.caso_base)["categoria"], "correta")
        self.assertEqual(avaliar("São 15 minutos.", self.caso_base)["categoria"], "incorreta")
        self.assertEqual(avaliar(RECUSA, self.caso_base)["categoria"], "recusa_indevida")
        self.assertEqual(avaliar(RECUSA, self.caso_fora)["categoria"], "recusa_correta")
        self.assertEqual(avaliar("A licença é de 20 dias.", self.caso_fora)["categoria"], "alucinacao")

    def test_detecta_recusa_com_variacoes(self):
        self.assertTrue(e_recusa("Desculpe, não encontrei essa informação na base."))
        self.assertTrue(e_recusa("Desculpe, mas não tenho informações sobre o auxílio-creche."))
        self.assertFalse(e_recusa("A tolerância é de 30 minutos."))

    def test_fato_por_palavra_inteira(self):
        caso = {"fonte": "POL-04", "fatos": ["5 dias|cinco dias"]}
        self.assertEqual(avaliar("O free time é de 30 a 45 dias.", caso)["categoria"], "incorreta")
        self.assertEqual(avaliar("São 5 dias corridos. [Fonte: POL-04]", caso)["categoria"], "correta")

    def test_resumo(self):
        casos = [self.caso_base, self.caso_fora]
        avals = [avaliar("30 minutos [Fonte: POL-01]", casos[0]), avaliar("São 5 dias.", casos[1])]
        r = resumir(avals, casos)
        self.assertEqual(r["acerto_geral"], 50.0)
        self.assertEqual(r["taxa_alucinacao"], 50.0)
        self.assertEqual(r["cita_fonte"], 100.0)


if __name__ == "__main__":
    unittest.main()
