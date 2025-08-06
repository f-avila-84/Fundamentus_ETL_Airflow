USE [FundamentosDB]
GO

/****** Object:  View [dbo].[vw_ranking_magic_formula]    Script Date: 05/08/2025 20:13:01 ******/
SET ANSI_NULLS ON
GO

SET QUOTED_IDENTIFIER ON
GO



-- DROP VIEW IF EXISTS vw_ranking_magic_formula; -- Descomente esta linha se precisar recriar a VIEW

/*

SELECT * FROM vw_ranking_magic_formula

*/

 ALTER VIEW [dbo].[vw_ranking_magic_formula] AS 

 WITH Metricas_Calculadas AS (
 
 SELECT 
		[ticker],
		[data_execucao],
		[tipo],
		[empresa],
		[setor], 
		[subsetor],
		[data_ult_cot],
		[cotacao],
		[vol_med_2m],
		[ev_ebit], 
		CAST([roic] AS FLOAT) AS [roic_clean], -------------------- APENAS PARA GARANTIR QUE A COLUNA ESTÁ COMO FLOAT
		CAST((1 / [ev_ebit]) AS FLOAT) AS [earnings_yield_clean] -- APENAS PARA GARANTIR QUE A COLUNA ESTÁ COMO FLOAT
   FROM [dbo].[fundamentus_historico]
  WHERE [data_execucao] = (SELECT MAX(data_execucao) FROM [dbo].[fundamentus_historico]) -- PEGA APENAS A ÚLTIMA INFORMAÇÃO
	AND [roic] IS NOT NULL
	AND [roic] > 0 ------------------------------------------------ NÃO ACEITAMOS ROIC NEGATIVO
	AND [ev_ebit] IS NOT NULL 
	AND [ev_ebit] > 0 --------------------------------------------- NÃO ACEITAMOS EV/EBIT NEGATIVO
	AND [vol_med_2m] >= 20000000 -- VOLUME NEGOCIADO MAIOR QUE R$ 10.000.000
	AND [subsetor] NOT IN ('Água e Saneamento','Incorporações','Construção Pesada','Energia Elétrica',
						   'Exploração de Imóveis','Gás','Holdings Diversificadas',
						   'Soc. Crédito e Financiamento','Bancos','Outros','Corretoras de Seguros',
						   'Seguradoras','Gestão de Recursos e Investimentos','Serviços Financeiros Diversos',
						   'Telecomunicações','Exploração de Rodovias','Serv.Méd.Hospit. Análises e Diagnósticos')
),


Empresas_Rankeadas AS (
 SELECT 
		[ticker],
		[data_execucao],
		[tipo],
		[empresa],
		[setor], 
		[subsetor],
		[data_ult_cot],
		[cotacao],
		[vol_med_2m],
		[ev_ebit], 
		[roic_clean], ---------------------------------------------------- QUANTO MAIOR, MELHOR. MAIS A EMPRESA VALE EM RELAÇÃO AO CAPITAL INVESTIDO
		RANK() OVER (ORDER BY [roic_clean] DESC) AS [rank_roic], --------- RANKEANDO DO MAIOR ROIC PARA O MENOR
		[earnings_yield_clean], ------------------------------------------ QUANTO MAIOR, MELHOR. MAIS A EMPRESA VALE EM A SUA DIVIDA
		RANK() OVER (ORDER BY [earnings_yield_clean] DESC) AS [rank_ey] -- RANKEANDO DO MAIOR EY PARA O MENOR 
   FROM [Metricas_Calculadas]
)



 SELECT TOP 1000
		[ticker],
		[data_execucao],
		[tipo],
		[empresa],
		[setor], -------------------- GREEMBLATT NAO APLICA A FORMULA EM BANCOS, SEGURADORAS E EMPRESAS DO SETOR PUBLICO
		[subsetor],
		[data_ult_cot],
		[cotacao],
		[vol_med_2m], --------------- PODEMOS INCLUIR UM FILTRO NO VOLUME NEGOCIADO, PARA GARANTIAR QUE SEJA UM EMRPESA COM LIQUIDEZ NO MERCADO
		[ev_ebit], 
		[earnings_yield_clean], ----- QUANTO MAIOR, MELHOR. MAIS A EMPRESA VALE EM A SUA DIVIDA
		[roic_clean], --------------- QUANTO MAIOR, MELHOR. MAIS A EMPRESA VALE EM RELAÇÃO AO CAPITAL INVESTIDO
		[rank_ey], ------------------ RANKEAR DO MAIOR EY PARA O MENOR 
		[rank_roic], ---------------- RANKEAR DO MAIOR ROIC PARA O MENOR
		([rank_ey] + [rank_roic]) AS [magic_formula_rank] 
   FROM [Empresas_Rankeadas]
ORDER BY [magic_formula_rank] ASC --- MENOR SOMA = MELHOR
  


GO

