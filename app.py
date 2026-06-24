import streamlit as st
import subprocess
import paramiko
import config
import socket
import os

REMOTE_HOST = config.REMOTE_SSH_HOST
REMOTE_USER = config.REMOTE_USER
SSH_KEY_PATH = config.SSH_KEY_PATH #os.path.expanduser("~/.ssh/id_rsa") # Adjust path if necessary
REMOTE_PING_HOST = config.REMOTE_PING_HOST

def resolve_host(hostname):
    """Resolve hostname, falling back to hostname.local for mDNS (macOS)."""
    try:
        socket.getaddrinfo(hostname, None)
        return hostname
    except socket.gaierror:
        return f"{hostname}.local"

def execute_wake_pc():
    """Executes the local Wake PC command."""
    command = "/Volumes/Home/dorigo_a/bin/wakepc"
    try:
        with st.spinner(f"Sending wake-up signal via: {command}"):
            # Using run with check=True to raise an error if the command fails
            result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
            return f"Success! Wake-up command executed. Output: {result.stdout.strip()}"
    except subprocess.CalledProcessError as e:
        return f"Error executing wake-up command (Exit Code {e.returncode}):\n{e.stderr.strip()}"
    except FileNotFoundError:
        return f"Error: The command '{command}' was not found. Please check the path."
    except Exception as e:
        return f"An unexpected error occurred: {e}"

def execute_poweroff_pc():
    """
    Connect to the remote Ubuntu node and execute 'sudo poweroff' as alvise.
    NOTE: This assumes SSH key authentication is set up and 'sudo poweroff' is configured to run without a password for 'alvise'.
    """
    client = paramiko.SSHClient()
    client.load_system_host_keys()
    client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    try:
        host = resolve_host(REMOTE_HOST)
        with st.spinner(f"Connecting to {REMOTE_USER}@{REMOTE_HOST} and shutting down PC..."):
            client.connect(host, username=REMOTE_USER, key_filename=SSH_KEY_PATH, timeout=10)

            stdin, stdout, stderr = client.exec_command("sudo poweroff")

            exit_status = stdout.channel.recv_exit_status()

            output = stdout.read().decode().strip()
            error = stderr.read().decode().strip()

            if exit_status == 0:
                return f"Success! PowerOFF command sent to {REMOTE_HOST}. Output: {output}"
            else:
                return f"PowerOFF command failed (Exit Code {exit_status}). Stderr: {error}"

    except paramiko.AuthenticationException:
        return "Authentication failed. Please check the SSH key path and permissions."
    except paramiko.SSHException as e:
        return f"Could not establish SSH connection or command failed: {e}"
    except Exception as e:
        return f"An unexpected error occurred: {e}"
    finally:
        client.close()

# --- Streamlit UI ---

def main():
    st.title("💻 PC Control Dashboard")
    st.markdown("Control your local and remote devices.")

    st.sidebar.header("Remote Node Info")
    st.sidebar.info(f"Target Node: `{REMOTE_HOST}` | User: `{REMOTE_USER}`")
    st.sidebar.warning("Ensure passwordless sudo for 'poweroff' is configured on the remote node.")

    # --- Wake PC Button ---
    if st.button("Wake PC", use_container_width=True, type="primary"):
        result = execute_wake_pc()
        st.session_state['last_action'] = f"Wake PC Result: {result}"
        st.rerun()

    # --- PowerOFF PC Button ---
    if st.button("PowerOFF PC", use_container_width=True, type="secondary"):
        st.session_state['confirm_poweroff'] = True

    if st.session_state.get('confirm_poweroff'):
        st.warning(f"Are you sure you want to switch off `{REMOTE_HOST}`?")
        col1, col2 = st.columns(2)
        if col1.button("Confirm poweroff", type="primary"):
            st.session_state.pop('confirm_poweroff', None)
            result = execute_poweroff_pc()
            st.session_state['last_action'] = f"PowerOFF PC Result: {result}"
            st.rerun()
        if col2.button("Cancel"):
            st.session_state.pop('confirm_poweroff', None)
            st.rerun()

    # Display the result of the last action
    if 'last_action' in st.session_state:
        st.subheader("Last Action Status")
        st.code(st.session_state['last_action'])

if __name__ == "__main__":
    main()