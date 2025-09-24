USE FundamentosDB

SELECT * FROM [dbo].[carga_fundamentus]

SELECT * FROM 
[dbo].[fundamentus_historico]
WHERE data_execucao = (SELECT MAX(data_execucao) FROM [dbo].[fundamentus_historico])

SELECT * FROM 
[dbo].[fundamentus_historico_BACKUP]
WHERE data_execucao = (SELECT MAX(data_execucao) FROM [dbo].[fundamentus_historico_BACKUP])


DROP TABLE [dbo].[fundamentus_historico_BACKUP]

SELECT * 
INTO [dbo].[fundamentus_historico_BACKUP]
FROM [dbo].[fundamentus_historico]



UPDATE [dbo].[fundamentus_historico]
SET data_execucao = '2025-08-22'
WHERE data_execucao = '2025-08-23'



UPDATE [dbo].[fundamentus_historico]
SET hora_execucao = '21:15:54'
WHERE data_execucao = '2025-09-18'



SELECT DISTINCT
data_execucao, 
hora_execucao
FROM [dbo].[fundamentus_historico]
ORDER BY 1 DESC 

