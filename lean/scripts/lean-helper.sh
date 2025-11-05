#!/bin/bash

# ==============================================================================
# LEAN Pod Helper Script
# ==============================================================================
#
# This script provides common commands for working inside the LEAN pod.
# All scripts and tools are available from inside the container.
#
# Usage:
#   Run from inside the pod after: docker-compose exec lean-engine bash
#
# ==============================================================================

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

show_banner() {
    echo -e "${BLUE}╔════════════════════════════════════════════════════════════╗${NC}"
    echo -e "${BLUE}║           LEAN Algorithmic Trading Pod                    ║${NC}"
    echo -e "${BLUE}║           Interactive Command Helper                      ║${NC}"
    echo -e "${BLUE}╚════════════════════════════════════════════════════════════╝${NC}"
    echo ""
}

show_status() {
    echo -e "${CYAN}Current Status:${NC}"
    echo -e "  📂 Working Directory: ${GREEN}$(pwd)${NC}"
    echo -e "  🐍 Python Version: ${GREEN}$(python --version 2>&1)${NC}"
    echo -e "  📦 Pip Location: ${GREEN}$(which pip)${NC}"
    echo -e "  ⏰ Time Zone: ${GREEN}$TZ${NC}"
    echo ""
}

show_menu() {
    echo -e "${CYAN}Available Commands:${NC}"
    echo ""
    echo -e "${YELLOW}Data Management:${NC}"
    echo -e "  ${GREEN}1${NC}) Download market data (YFinance)"
    echo -e "  ${GREEN}2${NC}) List downloaded data"
    echo -e "  ${GREEN}3${NC}) Verify data files"
    echo ""
    echo -e "${YELLOW}Backtesting:${NC}"
    echo -e "  ${GREEN}4${NC}) Run backtest (custom strategy)"
    echo -e "  ${GREEN}5${NC}) Run backtest (example strategy)"
    echo -e "  ${GREEN}6${NC}) View last backtest results"
    echo ""
    echo -e "${YELLOW}Configuration:${NC}"
    echo -e "  ${GREEN}7${NC}) List configurations"
    echo -e "  ${GREEN}8${NC}) Edit algorithm"
    echo -e "  ${GREEN}9${NC}) Check Python packages"
    echo ""
    echo -e "${YELLOW}Development:${NC}"
    echo -e "  ${GREEN}10${NC}) Python shell (IPython if available)"
    echo -e "  ${GREEN}11${NC}) Run custom Python script"
    echo ""
    echo -e "  ${GREEN}s${NC}) Show status"
    echo -e "  ${GREEN}h${NC}) Show this help"
    echo -e "  ${GREEN}q${NC}) Quit"
    echo ""
}

download_data() {
    echo -e "${CYAN}Downloading Market Data...${NC}"
    echo ""
    python /Lean/scripts/download_yfinance_data.py "$@"
}

list_data() {
    echo -e "${CYAN}Downloaded Data Files:${NC}"
    echo ""
    if [ -d "/Lean/data/custom" ]; then
        find /Lean/data/custom -name "*.csv" -type f -exec ls -lh {} \; | awk '{print $9, "("$5")"}'
        echo ""
        echo -e "Total: $(find /Lean/data/custom -name '*.csv' | wc -l) files"
    else
        echo -e "${YELLOW}No data directory found. Run option 1 to download data.${NC}"
    fi
    echo ""
}

verify_data() {
    echo -e "${CYAN}Verifying Data Files...${NC}"
    echo ""

    if [ ! -d "/Lean/data/custom" ]; then
        echo -e "${RED}❌ No data directory found${NC}"
        return 1
    fi

    for csv in /Lean/data/custom/*/*.csv; do
        if [ -f "$csv" ]; then
            lines=$(wc -l < "$csv")
            ticker=$(basename $(dirname "$csv"))
            echo -e "  ✓ $ticker: $lines bars"
        fi
    done
    echo ""
}

run_backtest() {
    local config_file="$1"

    echo -e "${CYAN}Running Backtest...${NC}"
    echo -e "Config: ${GREEN}$config_file${NC}"
    echo ""

    cd /Lean/Launcher/bin/Debug

    dotnet QuantConnect.Lean.Launcher.dll --config "$config_file"
}

list_configs() {
    echo -e "${CYAN}Available Configurations:${NC}"
    echo ""
    ls -lh /Lean/config/*.json 2>/dev/null | awk '{print "  " $9}' || echo -e "${YELLOW}No config files found${NC}"
    echo ""
}

check_packages() {
    echo -e "${CYAN}Installed Python Packages:${NC}"
    echo ""
    pip list | grep -E "(yfinance|pandas|numpy|scipy|requests)"
    echo ""
}

interactive_menu() {
    show_banner
    show_status

    while true; do
        show_menu
        read -p "Enter choice: " choice
        echo ""

        case $choice in
            1)
                download_data
                ;;
            2)
                list_data
                ;;
            3)
                verify_data
                ;;
            4)
                run_backtest "/Lean/config/config.custom.json"
                ;;
            5)
                run_backtest "/Lean/config/config.example.json"
                ;;
            6)
                echo -e "${CYAN}Last Backtest Results:${NC}"
                ls -lt /Results/*.json 2>/dev/null | head -5 || echo "No results found"
                echo ""
                ;;
            7)
                list_configs
                ;;
            8)
                echo -e "${CYAN}Opening algorithm in nano...${NC}"
                nano /Lean/Algorithm/custom_data_alert_strategy.py
                ;;
            9)
                check_packages
                ;;
            10)
                echo -e "${CYAN}Starting Python shell...${NC}"
                if command -v ipython &> /dev/null; then
                    ipython
                else
                    python
                fi
                ;;
            11)
                read -p "Enter script path: " script_path
                python "$script_path"
                ;;
            s|S)
                show_status
                ;;
            h|H)
                # Menu will be shown in next loop
                ;;
            q|Q)
                echo -e "${GREEN}Goodbye!${NC}"
                exit 0
                ;;
            *)
                echo -e "${RED}Invalid choice. Try again.${NC}"
                echo ""
                ;;
        esac

        read -p "Press Enter to continue..."
        clear
        show_banner
        show_status
    done
}

# ==============================================================================
# Main Script Logic
# ==============================================================================

case "${1:-menu}" in
    menu|--menu|-m)
        clear
        interactive_menu
        ;;
    download|--download|-d)
        download_data "${@:2}"
        ;;
    list|--list|-l)
        list_data
        ;;
    verify|--verify|-v)
        verify_data
        ;;
    backtest|--backtest|-b)
        run_backtest "${2:-/Lean/config/config.custom.json}"
        ;;
    status|--status|-s)
        show_banner
        show_status
        ;;
    help|--help|-h)
        show_banner
        echo "Usage: lean-helper [command] [options]"
        echo ""
        echo "Commands:"
        echo "  menu       Interactive menu (default)"
        echo "  download   Download market data"
        echo "  list       List downloaded data"
        echo "  verify     Verify data files"
        echo "  backtest   Run backtest"
        echo "  status     Show pod status"
        echo "  help       Show this help"
        echo ""
        ;;
    *)
        echo -e "${RED}Unknown command: $1${NC}"
        echo "Run 'lean-helper help' for usage"
        exit 1
        ;;
esac
