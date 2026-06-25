import streamlit as st
import subprocess
import paramiko
import config
import socket
import sys
import os

REMOTE_HOST      = config.REMOTE_SSH_HOST
REMOTE_USER      = config.REMOTE_USER
SSH_KEY_PATH     = config.SSH_KEY_PATH #os.path.expanduser("~/.ssh/id_rsa") # Adjust path if necessary
REMOTE_PING_HOST = config.REMOTE_PING_HOST
BROADCAST_IP     = config.BROADCAST_IP
MACADDR          = config.MACADDR

#_________________________________________________________________________________
# def resolve_host(hostname):
#     """Resolve hostname, falling back to hostname.local for mDNS (macOS)."""
#     try:
#         socket.getaddrinfo(hostname, None)
#         return hostname
#     except socket.gaierror:
#         return f"{hostname}.local"

#_________________________________________________________________________________
def ssh_host( ) -> bool:
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    try:
        #host = resolve_host(REMOTE_HOST)
        with st.spinner(f"Connecting to {REMOTE_USER}@{REMOTE_HOST} and to check host can execute commands..."):
            client.connect(REMOTE_HOST, username=REMOTE_USER, key_filename=SSH_KEY_PATH, timeout=10)

            stdin, stdout, stderr = client.exec_command("hostname -s")

            exit_status = stdout.channel.recv_exit_status()

            # output = stdout.read().decode().strip()
            # error = stderr.read().decode().strip()

            if exit_status == 0:
                return True
            else:
                return False

    except paramiko.AuthenticationException:
        return "Authentication failed. Please check the SSH key path and permissions."
    except paramiko.SSHException as e:
        return f"Could not establish SSH connection or command failed: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
    finally:
        client.close()

#_________________________________________________________________________________
def ping_host() -> bool:
    """Check if a host is reachable via ping."""
    try:
        # -c 1: send 1 packet
        # -W 1: wait 1 second for a response
        result = subprocess.run(
            ["ping", "-c", "1", "-W", "1", REMOTE_PING_HOST],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            check=False
        )
        return result.returncode == 0
    except Exception:
        return False

#_________________________________________________________________________________
def execute_wake_pc() -> str:
    """Executes the local Wake PC command."""
    command = f"wakeonlan -i {BROADCAST_IP} {MACADDR}"
    try:
        with st.spinner(f"Sending wake-up signal via: {command}"):
            # Using run with check=True to raise an error if the command fails
            print(f"Sending wake-up signal via: {command}")
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return f"Success! Wake-up command executed. Output: {result.stdout.strip()}"
    except subprocess.CalledProcessError as e:
        return f"Error executing wake-up command (Exit Code {e.returncode}):\n{e.stderr.strip()}"
    except FileNotFoundError:
        return f"Error: The command '{command}' was not found. Please check the path."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

#_________________________________________________________________________________
def execute_poweroff_pc() -> bool:
    """
    Connect to the remote Ubuntu node and execute 'sudo poweroff' as REMOTE_USER.
    NOTE: This assumes SSH key authentication is set up and 'sudo poweroff' is configured to run without a password for 'REMOTE_USER'.
    """
    # client = paramiko.SSHClient()
    # client.load_system_host_keys()
    # client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    remote_cmd = (
        f"sudo poweroff"
    )
    print(f"  SSH: {REMOTE_USER}@{REMOTE_HOST} \"{remote_cmd}\"", file=sys.stderr)
    result = subprocess.run(
        ["ssh", "-o", "BatchMode=yes", f"{REMOTE_USER}@{REMOTE_HOST}", remote_cmd],
        capture_output=True,
        text=True,
        timeout=15,
    )
    if result.returncode != 0:
        print(f"  SSH stderr: {result.stderr.strip()}", file=sys.stderr)
        return False
    return True

    # try:
    #     # host = resolve_host(REMOTE_HOST)
    #     with st.spinner(f"Connecting to {REMOTE_USER}@{REMOTE_HOST} and shutting down PC..."):
    #         #print(f"Connecting to {REMOTE_USER}@{REMOTE_HOST} and shutting down PC...")
            #client.connect(REMOTE_HOST, username=REMOTE_USER, key_filename=SSH_KEY_PATH, timeout=10)

    #         stdin, stdout, stderr = client.exec_command("sudo poweroff")

    #         exit_status = stdout.channel.recv_exit_status()

    #         output = stdout.read().decode().strip()
    #         error = stderr.read().decode().strip()

    #         if exit_status == 0:
    #             return f"Success! PowerOFF command sent to {REMOTE_HOST}. Output: {output}"
    #         else:
    #             return f"PowerOFF command failed (Exit Code {exit_status}). Stderr: {error}"

    # except paramiko.AuthenticationException:
    #     return "Authentication failed. Please check the SSH key path and permissions."
    # except paramiko.SSHException as e:
    #     return f"Could not establish SSH connection or command failed: {e}"
    # except Exception as e:
    #     return f"An unexpected error occurred: {e}"
    # finally:
    #     client.close()

#_________________________________________________________________________________
@st.fragment(run_every=5)
def show_remote_host_status():
    """Display the ping status of the remote host in the sidebar."""
    current_online = ping_host() and ssh_host()
    #current_ssh = 

    # Check if status changed to trigger a full rerun for the whole app (to enable/disable buttons)
    if 'is_online' in st.session_state and st.session_state['is_online'] is not None and st.session_state['is_online'] != current_online:
        st.session_state['is_online'] = current_online
        st.rerun()

    st.session_state['is_online'] = current_online
    status_text = "🟢 Online" if current_online else "🔴 Offline"
    st.markdown(f"**Host Status:** {status_text}")

#_________________________________________________________________________________
# --- Streamlit UI ---
def main():
    if 'is_online' not in st.session_state:
        st.session_state['is_online'] = None

    st.title("💻 PC Control Dashboard")
    st.markdown("Control your remote device.")

    st.sidebar.header("Remote Node Info")
    st.sidebar.info(f"Target Node: `{REMOTE_HOST}` | User: `{REMOTE_USER}`")
    st.sidebar.warning("Ensure passwordless sudo for 'poweroff' is configured on the remote node.")
    st.sidebar.markdown("---")
    show_remote_host_status()

    # --- Wake PC Button ---
    if st.button("Wake PC", use_container_width=True, type="primary"):
        result = execute_wake_pc()
        st.session_state['last_action'] = f"Wake PC Result: {result}"
        st.rerun()

    # --- PowerOFF PC Button ---
    is_online = st.session_state.get('is_online', False)

    if st.button("PowerOFF PC", use_container_width=True, type="secondary", disabled=not is_online):
        st.session_state['confirm_poweroff'] = True

    if st.session_state.get('confirm_poweroff'):
        st.warning(f"Are you sure you want to switch off `{REMOTE_HOST}`?")
        col1, col2 = st.columns(2)
        if col1.button("Confirm poweroff", type="primary", disabled=not is_online):
            st.session_state.pop('confirm_poweroff', None)
            result = execute_poweroff_pc()
            st.session_state['last_action'] = f"PowerOFF PC Result: command sent, action is asynchronouse. Wait for status change..."
            st.rerun()
        if col2.button("Cancel"):
            st.session_state.pop('confirm_poweroff', None)
            st.rerun()

    # If the user cancels or the host goes offline while the confirmation is visible, clean up
    if st.session_state.get('confirm_poweroff') and not is_online:
        st.session_state.pop('confirm_poweroff', None)
        st.rerun()

    # Display the result of the last action
    if 'last_action' in st.session_state:
        st.subheader("Last Action Status")
        st.code(st.session_state['last_action'])

#_________________________________________________________________________________
if __name__ == "__main__":
    main()
