# Аудит окружения — WSL2 для разработки KADIMA

## Статус

| Компонент | Статус | Действие |
|-----------|--------|----------|
| Ubuntu 24.04 | ✅ | — |
| Python 3.12.3 | ✅ | — |
| Git 2.43 | ✅ | — |
| Git LFS 3.4.1 | ✅ | — |
| Node 22.22 | ✅ | — |
| Disk 950 GB free | ✅ | — |
| WSLg GPU | ✅ | — |
| **pip** | ❌ | Нужно установить |
| **sudo access** | ❌ | Нужно настроить |
| **Memory 3.8 GB** | ⚠️ | Маловато, но терпимо |

---

## Что нужно сделать (3 шага)

### Шаг 1: Настроить sudo без пароля

Открой **PowerShell на Windows** (от имени администратора) и выполни:

```powershell
# Войти в WSL
wsl -e bash -c "echo 'lletp ALL=(ALL) NOPASSWD:ALL' | sudo tee /etc/sudoers.d/lletp"
```

Или внутри WSL:
```bash
# Если помнишь пароль wo1ginewo:
echo 'wo1ginewo' | sudo -S bash -c 'echo "lletp ALL=(ALL) NOPASSWD:ALL" > /etc/sudoers.d/lletp'
```

### Шаг 2: Установить pip и development tools

```bash
# Обновить пакеты
sudo apt-get update -qq

# Установить pip
sudo apt-get install -y -qq python3-pip python3-venv python3-dev

# Установить полезные инструменты
sudo apt-get install -y -qq build-essential libsqlite3-dev

# Проверить
pip3 --version
```

### Шаг 3: Установить Python-зависимости для KADIMA

```bash
# Основные пакеты
pip3 install --user \
  pytest pytest-cov \
  pyyaml \
  pandas \
  huggingface_hub datasets transformers

# Для PyQt (тестируем в WSL, запускаем на Windows)
pip3 install --user pyqt6

# Для API
pip3 install --user fastapi uvicorn httpx
```

---

## После настройки — проверка

```bash
# Должно всё работать:
python3 -m pip --version
python3 -c "import pytest; print('pytest OK')"
python3 -c "import yaml; print('yaml OK')"
python3 -c "import pandas; print('pandas OK')"
python3 -c "import PyQt6; print('PyQt6 OK')" 2>/dev/null || echo "PyQt6: GUI only, OK for headless"
```

---

## Опционально (для максимальной эффективности)

### Добавить swap (3.8 GB RAM мало для тяжёлых задач)

```bash
sudo fallocate -l 4G /swapfile
sudo chmod 600 /swapfile
sudo mkswap /swapfile
sudo swapon /swapfile
echo '/swapfile none swap sw 0 0' | sudo tee -a /etc/fstab
free -h  # проверить: должно быть ~8 GB total
```

### Настроить git credential helper (не вводить токен каждый раз)

```bash
git config --global credential.helper store
# При первом push git спросит username/password — введи токен
# Сохранится в ~/.git-credentials
```

### Установить VS Code Remote WSL (для просмотра кода)

На Windows: установить расширение "Remote - WSL" в VS Code.
Затем: `code .` из WSL откроет проект в VS Code на Windows.
