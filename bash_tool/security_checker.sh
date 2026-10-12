#!/usr/bin/env bash
# =============================================================================
# security_checker.sh — Linux Security Checker
# =============================================================================
# Description : A read-only security checker for Linux systems.
#               It inspects the system for common security concerns and
#               reports PASS, WARNING, or INFO results. It never modifies
#               any system settings.
#
# Author      : IqraSec Internship — Phase 1
# Version     : 1.0.0
# Bash        : Requires Bash 4.0 or later
#
# Usage       : bash security_checker.sh [OPTION] [PATH]
# =============================================================================

# ---------------------------------------------------------------------------
# Script metadata
# ---------------------------------------------------------------------------
SCRIPT_VERSION="1.0.0"
SCRIPT_NAME="Linux Security Checker"

# ---------------------------------------------------------------------------
# Colour codes for readable terminal output
# Colours are only used when the terminal supports them.
# ---------------------------------------------------------------------------
if [ -t 1 ]; then
    RED='\033[0;31m'
    YELLOW='\033[1;33m'
    GREEN='\033[0;32m'
    CYAN='\033[0;36m'
    BOLD='\033[1m'
    RESET='\033[0m'
else
    # No colour if output is piped or redirected
    RED='' YELLOW='' GREEN='' CYAN='' BOLD='' RESET=''
fi

# ---------------------------------------------------------------------------
# Helper functions — print labelled output lines
# ---------------------------------------------------------------------------

print_header() {
    # Print a section header with a divider line
    echo ""
    echo -e "${BOLD}${CYAN}========================================${RESET}"
    echo -e "${BOLD}${CYAN}  $1${RESET}"
    echo -e "${BOLD}${CYAN}========================================${RESET}"
}

print_pass() {
    # PASS  = the check completed and the result looks good
    echo -e "  ${GREEN}[PASS]${RESET}    $1"
}

print_warning() {
    # WARNING = the check completed but found something worth reviewing
    echo -e "  ${YELLOW}[WARNING]${RESET} $1"
}

print_info() {
    # INFO  = informational result — no judgement implied
    echo -e "  ${CYAN}[INFO]${RESET}    $1"
}

print_error() {
    # ERROR  = the check could NOT be completed (e.g. missing command, no permission)
    echo -e "  ${RED}[ERROR]${RESET}   $1"
}

print_recommendation() {
    # Print an indented recommendation under a WARNING
    echo -e "             ${YELLOW}→ Recommendation:${RESET} $1"
}

# ---------------------------------------------------------------------------
# show_help — display usage information and exit
# ---------------------------------------------------------------------------
show_help() {
    echo ""
    echo -e "${BOLD}${SCRIPT_NAME} v${SCRIPT_VERSION}${RESET}"
    echo ""
    echo "DESCRIPTION"
    echo "  A read-only Linux security checker that inspects common security"
    echo "  indicators and reports PASS, WARNING, or INFO results."
    echo "  It never modifies any system settings."
    echo ""
    echo "USAGE"
    echo "  bash security_checker.sh [OPTION] [PATH]"
    echo ""
    echo "OPTIONS"
    echo "  --help              Show this help message and exit."
    echo "  --version           Show the version number and exit."
    echo "  --all               Run all available checks."
    echo "  --system            Show current user and OS information."
    echo "  --disk              Show disk usage for all mounted filesystems."
    echo "  --memory            Show current memory and swap usage."
    echo "  --firewall          Show firewall status (read-only)."
    echo "  --services          List actively running systemd services."
    echo "  --permissions PATH  Check PATH for world-writable files."
    echo ""
    echo "EXAMPLES"
    echo "  bash security_checker.sh --help"
    echo "  bash security_checker.sh --all"
    echo "  bash security_checker.sh --system"
    echo "  bash security_checker.sh --disk"
    echo "  bash security_checker.sh --memory"
    echo "  bash security_checker.sh --firewall"
    echo "  bash security_checker.sh --services"
    echo "  bash security_checker.sh --permissions /tmp"
    echo "  bash security_checker.sh --permissions /home"
    echo ""
    echo "NOTES"
    echo "  • All checks are read-only. No system settings are changed."
    echo "  • Some checks require elevated privileges; a message will be shown"
    echo "    when a check cannot be completed due to permissions."
    echo "  • Do not run this script against systems you do not own."
    echo ""
}

# ---------------------------------------------------------------------------
# show_version — print version string and exit
# ---------------------------------------------------------------------------
show_version() {
    echo "${SCRIPT_NAME} v${SCRIPT_VERSION}"
}

# ---------------------------------------------------------------------------
# check_system — display current user, hostname, OS, and kernel information
# ---------------------------------------------------------------------------
check_system() {
    print_header "System Information"

    # Current logged-in user
    local current_user
    current_user=$(whoami 2>/dev/null) || current_user="unknown"
    print_info "Current user   : ${current_user}"

    # Warn if running as root — root is a high-privilege account
    if [ "${current_user}" = "root" ]; then
        print_warning "You are running as root. Avoid using root for everyday tasks."
        print_recommendation "Create a regular user account for daily work."
    else
        print_pass "Running as a non-root user (${current_user})."
    fi

    # Hostname
    local hostname
    hostname=$(hostname 2>/dev/null) || hostname="unknown"
    print_info "Hostname       : ${hostname}"

    # Operating system name and version
    if [ -f /etc/os-release ]; then
        # /etc/os-release is the standard way to identify a Linux distro
        local os_name
        os_name=$(grep -E "^PRETTY_NAME=" /etc/os-release | cut -d= -f2 | tr -d '"')
        print_info "OS             : ${os_name}"
    else
        print_info "OS             : $(uname -o 2>/dev/null || echo 'unknown')"
    fi

    # Kernel version — useful to know for patch status
    local kernel
    kernel=$(uname -r 2>/dev/null) || kernel="unknown"
    print_info "Kernel version : ${kernel}"

    # System uptime — how long since last reboot
    if command -v uptime &>/dev/null; then
        local uptime_str
        uptime_str=$(uptime -p 2>/dev/null || uptime 2>/dev/null)
        print_info "Uptime         : ${uptime_str}"
    else
        print_error "Could not determine uptime ('uptime' command not found)."
    fi
}

# ---------------------------------------------------------------------------
# check_disk — show disk usage; warn on high-usage filesystems
# ---------------------------------------------------------------------------
check_disk() {
    print_header "Disk Usage"

    # df -h gives human-readable sizes; --output selects specific columns
    # We skip the tmpfs and devtmpfs virtual filesystems (not real storage)
    if ! command -v df &>/dev/null; then
        print_error "The 'df' command is not available. Cannot check disk usage."
        return
    fi

    print_info "Disk usage for all real mounted filesystems:"
    echo ""

    # Read each line of df output (skip the header with NR>1)
    # Fields: filesystem, size, used, available, use%, mount-point
    df -h --output=source,size,used,avail,pcent,target 2>/dev/null \
        | grep -v "^Filesystem\|^tmpfs\|^devtmpfs\|^udev\|^none\|^overlay" \
        | while IFS= read -r line; do
            echo "    ${line}"
        done

    echo ""

    # Now check each filesystem's usage percentage and warn if high.
    # We include 'source' so the grep filter can exclude virtual filesystems
    # (tmpfs, devtmpfs, udev, overlay, none).  Fields: source, pcent, target.
    df -h --output=source,pcent,target 2>/dev/null \
        | grep -v "^Filesystem\|^tmpfs\|^devtmpfs\|^udev\|^none\|^overlay" \
        | while IFS= read -r line; do
            # Extract the percentage number (field 2) and mount point (field 3)
            local pct mount
            pct=$(echo "${line}" | awk '{print $2}' | tr -d '%')
            mount=$(echo "${line}" | awk '{print $3}')

            # Skip blank lines
            [ -z "${pct}" ] && continue

            if [ "${pct}" -ge 90 ] 2>/dev/null; then
                print_warning "Filesystem '${mount}' is ${pct}% full."
                print_recommendation "Free up space or expand the filesystem to avoid failures."
            elif [ "${pct}" -ge 75 ] 2>/dev/null; then
                print_warning "Filesystem '${mount}' is ${pct}% full (getting high)."
                print_recommendation "Monitor usage and consider cleanup."
            else
                print_pass "Filesystem '${mount}' usage is ${pct}% — within safe limits."
            fi
        done
}

# ---------------------------------------------------------------------------
# check_memory — show RAM and swap usage
# ---------------------------------------------------------------------------
check_memory() {
    print_header "Memory & Swap Usage"

    if ! command -v free &>/dev/null; then
        print_error "The 'free' command is not available. Cannot check memory."
        return
    fi

    # free -h gives human-readable output
    print_info "Current memory status:"
    echo ""
    free -h 2>/dev/null | while IFS= read -r line; do
        echo "    ${line}"
    done
    echo ""

    # Check RAM usage percentage
    # free -m gives values in megabytes — easier for arithmetic
    local total_ram used_ram pct_ram
    total_ram=$(free -m 2>/dev/null | awk '/^Mem:/{print $2}')
    used_ram=$(free -m 2>/dev/null  | awk '/^Mem:/{print $3}')

    if [ -n "${total_ram}" ] && [ "${total_ram}" -gt 0 ] 2>/dev/null; then
        # Calculate percentage used (integer arithmetic)
        pct_ram=$(( used_ram * 100 / total_ram ))
        if [ "${pct_ram}" -ge 90 ]; then
            print_warning "RAM usage is ${pct_ram}% (${used_ram}MB / ${total_ram}MB)."
            print_recommendation "Investigate memory-hungry processes with 'top' or 'htop'."
        elif [ "${pct_ram}" -ge 75 ]; then
            print_warning "RAM usage is elevated at ${pct_ram}% (${used_ram}MB / ${total_ram}MB)."
        else
            print_pass "RAM usage is ${pct_ram}% (${used_ram}MB / ${total_ram}MB) — normal."
        fi
    else
        print_error "Could not parse RAM usage values."
    fi

    # Check swap usage
    local total_swap used_swap
    total_swap=$(free -m 2>/dev/null | awk '/^Swap:/{print $2}')
    used_swap=$(free -m 2>/dev/null  | awk '/^Swap:/{print $3}')

    if [ -n "${total_swap}" ] && [ "${total_swap}" -gt 0 ] 2>/dev/null; then
        local pct_swap
        pct_swap=$(( used_swap * 100 / total_swap ))
        if [ "${pct_swap}" -ge 50 ]; then
            print_warning "Swap usage is ${pct_swap}% — heavy swap use slows the system."
            print_recommendation "Consider adding more RAM or reducing memory pressure."
        else
            print_pass "Swap usage is ${pct_swap}% — acceptable."
        fi
    else
        print_info "No swap space configured or swap is zero."
    fi
}

# ---------------------------------------------------------------------------
# check_firewall — show firewall status; never modifies any rules
# ---------------------------------------------------------------------------
check_firewall() {
    print_header "Firewall Status"

    local firewall_found=false

    # --- Check UFW (Uncomplicated Firewall) ---
    if command -v ufw &>/dev/null; then
        firewall_found=true
        print_info "UFW (Uncomplicated Firewall) is installed."
        # ufw status may require root; capture the output and handle gracefully
        local ufw_status
        ufw_status=$(ufw status 2>/dev/null)
        if echo "${ufw_status}" | grep -qi "active"; then
            print_pass "UFW is active and running."
            print_info "UFW rules summary:"
            echo "${ufw_status}" | while IFS= read -r line; do
                echo "    ${line}"
            done
        elif echo "${ufw_status}" | grep -qi "inactive"; then
            print_warning "UFW is installed but currently INACTIVE (disabled)."
            print_recommendation "Enable UFW with 'sudo ufw enable' to protect the system."
        else
            print_error "Could not determine UFW status (permission denied or unexpected output)."
            print_info "Try running: sudo ufw status"
        fi
    fi

    # --- Check firewalld ---
    if command -v firewall-cmd &>/dev/null; then
        firewall_found=true
        print_info "firewalld is installed."
        local fwd_state
        fwd_state=$(firewall-cmd --state 2>/dev/null)
        if [ "${fwd_state}" = "running" ]; then
            print_pass "firewalld is running."
        else
            print_warning "firewalld is installed but not running (state: ${fwd_state:-unknown})."
            print_recommendation "Start firewalld with 'sudo systemctl start firewalld'."
        fi
    fi

    # --- Check iptables ---
    if command -v iptables &>/dev/null; then
        firewall_found=true
        print_info "iptables is available on this system."
        # Count the number of rules in the INPUT chain
        local rule_count
        rule_count=$(iptables -L INPUT --line-numbers 2>/dev/null | grep -c "^[0-9]") || rule_count="unknown"
        if [ "${rule_count}" = "unknown" ]; then
            print_error "Could not read iptables rules (likely need root privileges)."
            print_info "Try: sudo iptables -L -n -v"
        elif [ "${rule_count}" -eq 0 ] 2>/dev/null; then
            print_warning "iptables INPUT chain has no custom rules — traffic may be unrestricted."
            print_recommendation "Review and set iptables rules appropriate for this system's role."
        else
            print_pass "iptables INPUT chain has ${rule_count} rule(s) defined."
            print_info "Run 'sudo iptables -L -n -v' to review all rules."
        fi
    fi

    # --- No firewall tool found ---
    if [ "${firewall_found}" = false ]; then
        print_warning "No recognised firewall tool found (ufw, firewall-cmd, iptables)."
        print_recommendation "Install and configure a firewall to protect network services."
    fi
}

# ---------------------------------------------------------------------------
# check_services — list running systemd services (read-only)
# ---------------------------------------------------------------------------
check_services() {
    print_header "Running Services"

    if ! command -v systemctl &>/dev/null; then
        print_error "'systemctl' is not available on this system."
        # Try the older 'service' command as a fallback
        if command -v service &>/dev/null; then
            print_info "Attempting fallback with 'service --status-all' ..."
            service --status-all 2>/dev/null || print_error "Could not list services."
        fi
        return
    fi

    # List services that are currently running (state=running)
    print_info "Services currently in 'running' state:"
    echo ""

    local service_list
    service_list=$(systemctl list-units --type=service --state=running \
                   --no-legend --no-pager 2>/dev/null)

    if [ -z "${service_list}" ]; then
        print_warning "No running services detected or insufficient permissions."
        print_info "Try: sudo systemctl list-units --type=service --state=running"
    else
        # Count running services
        local count
        count=$(echo "${service_list}" | grep -c ".")
        print_info "Total running services: ${count}"
        echo ""
        echo "${service_list}" | while IFS= read -r line; do
            echo "    ${line}"
        done
        echo ""
        print_pass "Service list retrieved successfully."
        print_info "Review the list above and disable any services not needed on this machine."
        print_recommendation "Use 'sudo systemctl disable <service>' to prevent unused services from starting."
    fi
}

# ---------------------------------------------------------------------------
# check_permissions PATH — find world-writable files in a given directory
# ---------------------------------------------------------------------------
check_permissions() {
    local target_path="$1"

    print_header "World-Writable File Check"
    print_info "Scanning directory: ${target_path}"

    # --- Validate the path ---
    if [ -z "${target_path}" ]; then
        print_error "No path provided. Usage: --permissions /path/to/directory"
        return 1
    fi

    if [ ! -e "${target_path}" ]; then
        print_error "Path does not exist: ${target_path}"
        return 1
    fi

    if [ ! -d "${target_path}" ]; then
        print_error "Path is not a directory: ${target_path}"
        return 1
    fi

    if [ ! -r "${target_path}" ]; then
        print_error "Cannot read directory: ${target_path} (permission denied)"
        return 1
    fi

    echo ""
    print_info "Searching for world-writable files (this may take a moment)..."
    echo ""

    # --- Find world-writable files ---
    # -perm -o+w  : files that are writable by 'others' (world-writable)
    # ! -type l   : skip symbolic links (they often appear world-writable)
    # 2>/dev/null : suppress "Permission denied" errors for subdirectories
    local ww_files
    ww_files=$(find "${target_path}" \
                    -perm -o+w \
                    ! -type l \
                    2>/dev/null)

    if [ -z "${ww_files}" ]; then
        print_pass "No world-writable files found in '${target_path}'."
    else
        # Count how many were found
        local count
        count=$(echo "${ww_files}" | grep -c ".")
        print_warning "${count} world-writable file(s) found in '${target_path}':"
        echo ""
        echo "${ww_files}" | while IFS= read -r filepath; do
            # Show the permissions alongside the path for context
            local perms
            perms=$(stat -c "%a %A" "${filepath}" 2>/dev/null || echo "???")
            echo -e "    ${YELLOW}${perms}${RESET}  ${filepath}"
        done
        echo ""
        print_recommendation "Review each file above. Use 'chmod o-w <file>' to remove world-write."
        print_recommendation "Note: /tmp is intentionally world-writable on most systems."
    fi

    # --- Also check for SUID/SGID files as a bonus security check ---
    echo ""
    print_info "Bonus: Checking for SUID/SGID files in '${target_path}' ..."
    local suid_files
    suid_files=$(find "${target_path}" \
                      \( -perm -4000 -o -perm -2000 \) \
                      -type f \
                      2>/dev/null)
    if [ -z "${suid_files}" ]; then
        print_pass "No SUID/SGID files found in '${target_path}'."
    else
        local suid_count
        suid_count=$(echo "${suid_files}" | grep -c ".")
        print_warning "${suid_count} SUID/SGID file(s) found:"
        echo "${suid_files}" | while IFS= read -r filepath; do
            local perms
            perms=$(stat -c "%a %A" "${filepath}" 2>/dev/null || echo "???")
            echo -e "    ${YELLOW}${perms}${RESET}  ${filepath}"
        done
        print_recommendation "SUID/SGID files can be a privilege-escalation risk. Review them carefully."
    fi
}

# ---------------------------------------------------------------------------
# run_all — run every available check in sequence
# ---------------------------------------------------------------------------
run_all() {
    print_header "Running All Security Checks"
    check_system
    check_disk
    check_memory
    check_firewall
    check_services
    # Default permissions check on /tmp when running --all
    check_permissions "/tmp"
}

# ===========================================================================
# MAIN — parse command-line arguments and dispatch to the correct function
# ===========================================================================
main() {
    # Show help if no arguments are provided
    if [ "$#" -eq 0 ]; then
        echo ""
        echo -e "${YELLOW}No option specified. Use --help to see available options.${RESET}"
        echo "  Example: bash security_checker.sh --help"
        echo ""
        exit 0
    fi

    # Parse the first argument
    local option="$1"

    case "${option}" in
        --help | -h)
            show_help
            ;;
        --version | -v)
            show_version
            ;;
        --all)
            run_all
            ;;
        --system)
            check_system
            ;;
        --disk)
            check_disk
            ;;
        --memory)
            check_memory
            ;;
        --firewall)
            check_firewall
            ;;
        --services)
            check_services
            ;;
        --permissions)
            # The path is the second argument
            local path_arg="$2"
            if [ -z "${path_arg}" ]; then
                echo ""
                print_error "Usage: --permissions <PATH>"
                echo "  Example: bash security_checker.sh --permissions /tmp"
                echo ""
                exit 1
            fi
            check_permissions "${path_arg}"
            ;;
        *)
            echo ""
            echo -e "${RED}Unknown option: ${option}${RESET}"
            echo "Run 'bash security_checker.sh --help' to see valid options."
            echo ""
            exit 1
            ;;
    esac

    # Capture the exit status of the last sub-command before printing the footer.
    # This allows the script to return exit code 1 when, for example,
    # --permissions is given a nonexistent path (check_permissions returns 1).
    local cmd_exit=$?

    # Print a footer with a timestamp
    echo ""
    echo -e "${CYAN}--- Check completed: $(date '+%Y-%m-%d %H:%M:%S %Z') ---${RESET}"
    echo ""

    # Exit with the sub-command's exit status so callers can detect errors
    exit "${cmd_exit}"
}

# Run main with all arguments passed to the script
main "$@"
