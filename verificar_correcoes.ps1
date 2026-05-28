Write-Host "=== Verificando correções P0/P1 ===" -ForegroundColor Cyan

# 1. Verificar configurações
Write-Host "
1. Verificando Settings..." -ForegroundColor Yellow
python -c "from src.config import settings; print(f'✓ Settings carregado: env={settings.env}, is_production={settings.is_production}')" 2>&1

# 2. Verificar importações
Write-Host "
2. Verificando importações..." -ForegroundColor Yellow
python -c "from src.main import app; print('✓ Main carregado com routers')" 2>&1

# 3. Verificar use cases
Write-Host "
3. Verificando use cases..." -ForegroundColor Yellow
python -c "from src.application.use_cases.processar_webhook_use_case import ProcessarWebhookUseCase, ProcessarWebhookOutput; print('✓ Webhook use case OK')" 2>&1
python -c "from src.application.use_cases.reprocessar_pendentes_use_case import ReprocessarPendentesUseCase; print('✓ Reprocessar use case OK')" 2>&1

# 4. Rodar linter
Write-Host "
4. Rodando Ruff..." -ForegroundColor Yellow
ruff check src --fix

# 5. Rodar type checker
Write-Host "
5. Rodando Mypy..." -ForegroundColor Yellow
mypy src --ignore-missing-imports

# 6. Rodar testes
Write-Host "
6. Rodando testes..." -ForegroundColor Yellow
pytest tests/ -v --tb=short

Write-Host "
=== Verificação concluída ===" -ForegroundColor Green
