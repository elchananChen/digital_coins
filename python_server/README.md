# warning !!

heavy process - need strong cpu !

<!-- structure -->

└── [X] 📁 python_server
├── [X] 📄 .env
├── [X] 📄 .gitignore
├── [X] 📄 README.md
├── [X] 📁 core
│ ├── [X] 📄 **init**.py
│ ├── [X] 📄 db.py
│ ├── [X] 📄 models.py
│ └── [X] 📄 monitor.py
├── [X] 📁 exchanges
│ ├── [X] 📄 **init**.py
│ ├── [X] 📄 binance.py
│ ├── [X] 📄 by_bit.py
│ └── [X] 📄 kraken.py
├── [X] 📁 graphs
│ ├── [X] 📄 monitor_graph.py
│ └── [X] 📄 monitor_log.csv
├── [X] 📄 main.py
├── [X] 📄 poetry.lock
├── [X] 📄 pyproject.toml
└── [X] 📁 utils
├── [X] 📄 **init**.py
└── [X] 📄 scraping_utils.py

# run the project:

poetry run python main.py

# run the monitor graph:

poetry run python graphs/monitor_graph.py

# exchanges urls

# binance, kraken, by bit, crypto.com , bit stamp, coinbase

https://www.binance.com/en/trade/BTC_USDT?_from=markets&type=spot
https://pro.kraken.com/app/trade/btc-usd
https://www.bybit.com/en/trade/spot/BTC/USDT

<!-- installation -->

## Installing Poetry

### Windows

#### Method 1: Using PowerShell (global installation) (Recommended)

1. Open PowerShell as Administrator
2. Run the following command:

```powershell
(Invoke-WebRequest -Uri https://install.python-poetry.org -UseBasicParsing).Content | py -
```

#### Method 2: Using pip (local installation)

```powershell
pip install poetry
```

#### Adding Poetry to PATH (Windows)

After installation, you may need to add Poetry to PATH:

1. Search for "Environment Variables" in the Start menu
2. Click on "Edit the system environment variables"
3. Click on "Environment Variables"
4. Under "User variables", find "Path" and click "Edit"
5. Add the path: `%APPDATA%\Python\Scripts`

### macOS

#### Method 1: Using curl (Recommended)

Open Terminal and run:

```bash
curl -sSL https://install.python-poetry.org | python3 -
```

#### Method 2: Using Homebrew

```bash
brew install poetry
```

#### Method 3: Using pip

```bash
pip3 install poetry
```

#### Adding Poetry to PATH (macOS)

Add the following line to your `~/.zshrc` or `~/.bash_profile` file:

```bash
export PATH="$HOME/.local/bin:$PATH"
```

Then run:

```bash
source ~/.zshrc
```

## Running the Project

**Important**: Make sure your terminal is in the `python_server` directory (where the `pyproject.toml` file is located)

### 2. Install Dependencies

```bash
poetry install
```

### 3. Set Environment Variables

Create a `.env` file in the project directory with the following content:

```
DB_URI=your_mongodb_connection_string
```

### 4. Install Playwright Browsers

```bash
poetry run playwright install
```

### 5. Run the Project

```bash
poetry run python main.py
```

## Verifying Installation

To check that Poetry was installed successfully:

```bash
poetry --version
```

To check that the project is ready to run:

```bash
poetry check
```

## Common Troubleshooting

### Windows

- If `poetry` is not recognized as a command, try closing and reopening PowerShell
- Make sure Python is installed on your system
- If there are PATH issues, try opening PowerShell as Administrator

### macOS

- If there are permission issues, try adding `sudo` before commands
- Make sure Xcode Command Line Tools are installed: `xcode-select --install`
- If using zsh, make sure changes are saved in `~/.zshrc`

## Technical Information

The project uses:

- **Python 3.11+**
- **Playwright** for scraping data from Binance
- **Beanie & Motor** for working with MongoDB
- **Schedule** for scheduled tasks

Supported cryptocurrencies: BTC, ETH, LTC, XRP, BCH

---

If you encounter issues, make sure that:

1. Your terminal is in the correct project directory
2. Python 3.11+ is installed
3. Poetry is installed and in PATH
4. The `.env` file is configured with database connection details
