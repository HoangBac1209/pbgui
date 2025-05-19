import streamlit as st
import platform
from pbgui_func import check_password, set_page_config, change_ini, is_pb7_installed, is_pb_installed, is_authenticted, get_navi_paths
from pbgui_purefunc import load_ini, save_ini
import pbgui_help
from Services import Services
from Instance import Instances
from RunV7 import V7Instances
from Multi import MultiInstances
from User import Users
from PBCoinData import CoinData
import toml
import os
from pathlib import Path, PurePath

def change_password():
    with st.expander("Change Password"):
        with st.form("change_password_form"):
            current_password = st.text_input("Current Password", type="password", placeholder="Enter current password", help=pbgui_help.change_password)
            new_password = st.text_input("New Password", type="password", placeholder="Enter new password", help=pbgui_help.change_password)
            confirm_password = st.text_input("Confirm New Password", type="password", placeholder="Re-enter new password", help=pbgui_help.change_password)
            submit_button = st.form_submit_button("Update Password", help=pbgui_help.change_password)

        if submit_button:
            stored_password = st.secrets.get("password", "")
            if current_password != stored_password:
                st.error("Current password is incorrect.")
                return
            if new_password != confirm_password:
                st.error("New passwords do not match.")
                return
            try:
                secrets_path = Path(".streamlit/secrets.toml")
                if not secrets_path.exists():
                    st.error("secrets.toml file does not exist.")
                    with open(secrets_path, "w") as f:
                        f.write("")
                with open(secrets_path, "r") as f:
                    try:
                        secrets = toml.load(f)
                    except toml.TomlDecodeError:
                        st.error("secrets.toml is not a valid TOML file.")
                        return
                secrets["password"] = new_password
                with open(secrets_path, "w") as f:
                    toml.dump(secrets, f)
                st.success("Password updated successfully. Please log in again.")
                st.session_state.clear()
                st.rerun()
            except Exception as e:
                st.error(f"An error occurred while updating the password: {e}")

def is_configured():
    """Check if all required configurations are valid, including both Passivbot V6 and V7 if installed."""
    pbdir = load_ini("main", "pbdir")
    pbvenv = load_ini("main", "pbvenv")
    pb7dir = load_ini("main", "pb7dir")
    pb7venv = load_ini("main", "pb7venv")
    pbname = load_ini("main", "pbname")
    role = load_ini("main", "role")

    # Initialize Users and CoinData for validation
    users = Users()
    coin_data = CoinData()

    # Check Passivbot V6 configuration
    if pbdir and pbdir.strip() != "":
        # Check if path exists
        if not Path(pbdir).exists():
            st.session_state.config_error = f"Passivbot V6 path '{pbdir}' does not exist."
            return False
        # Check if passivbot.py exists
        if not Path(f"{pbdir}/passivbot.py").exists():
            st.session_state.config_error = f"Passivbot V6 path '{pbdir}' is missing passivbot.py."
            return False
        # Check if venv is configured
        if not pbvenv or pbvenv.strip() == "":
            st.session_state.config_error = "Passivbot V6 venv is not configured."
            return False
        # Check if venv is a valid file
        if not Path(pbvenv).is_file():
            st.session_state.config_error = f"Passivbot V6 venv '{pbvenv}' is not a valid file."
            return False
        # Check if venv is a valid Python interpreter
        if not PurePath(pbvenv).name.startswith("python"):
            st.session_state.config_error = f"Passivbot V6 venv '{pbvenv}' is not a valid Python interpreter."
            return False
    else:
        st.session_state.config_error = "Passivbot V6 path is not configured."
        return False

    # Check Passivbot V7 configuration
    if pb7dir and pb7dir.strip() != "":
        # Check if path exists
        if not Path(pb7dir).exists():
            st.session_state.config_error = f"Passivbot V7 path '{pb7dir}' does not exist."
            return False
        # Check if src/passivbot.py exists
        if not Path(f"{pb7dir}/src/passivbot.py").exists():
            st.session_state.config_error = f"Passivbot V7 path '{pb7dir}' is missing src/passivbot.py."
            return False
        # Check if venv is configured
        if not pb7venv or pb7venv.strip() == "":
            st.session_state.config_error = "Passivbot V7 venv is not configured."
            return False
        # Check if venv is a valid file
        if not Path(pb7venv).is_file():
            st.session_state.config_error = f"Passivbot V7 venv '{pb7venv}' is not a valid file."
            return False
        # Check if venv is a valid Python interpreter
        if not PurePath(pb7venv).name.startswith("python"):
            st.session_state.config_error = f"Passivbot V7 venv '{pb7venv}' is not a valid Python interpreter."
            return False
    else:
        st.session_state.config_error = "Passivbot V7 path is not configured."
        return False

    # Check bot name
    if not pbname or pbname.strip() == "":
        st.session_state.config_error = "Bot name is not configured or empty."
        return False

    # Check role
    if not role or role not in ["master", "slave"]:
        st.session_state.config_error = "Role (master/slave) is not configured or invalid."
        return False

    # Check users
    if not users.list():
        st.session_state.config_error = "No users are configured. Please configure at least one user in Setup API-Keys."
        return False

    # Check Coin Data API
    if not coin_data.fetch_api_status():
        st.session_state.config_error = "Coin Data API is not configured. Please configure it in Coin Data."
        return False

    # Clear config error if all checks pass
    if "config_error" in st.session_state:
        del st.session_state.config_error
    return True

def do_init():
    if "password_missing" in st.session_state:
        st.warning('You are using PBGUI without a password! Please set a password using "Change Password" below.', icon="⚠️")
    
    if "input_pbdir" in st.session_state:
        if st.session_state.input_pbdir != st.session_state.pbdir:
            st.session_state.pbdir = st.session_state.input_pbdir
            save_ini("main", "pbdir", st.session_state.pbdir)
            if "users" in st.session_state:
                del st.session_state.users
    st.session_state.pbdir = load_ini("main", "pbdir")
    if ".." in st.session_state.pbdir:
        st.session_state.pbdir = os.path.abspath(st.session_state.pbdir)
        save_ini("main", "pbdir", st.session_state.pbdir)
    pbdir_ok = "✅" if st.session_state.pbdir and Path(f"{st.session_state.pbdir}/passivbot.py").exists() else "❌"

    if "input_pbvenv" in st.session_state:
        if st.session_state.input_pbvenv != st.session_state.pbvenv:
            st.session_state.pbvenv = st.session_state.input_pbvenv
            save_ini("main", "pbvenv", st.session_state.pbvenv)
    st.session_state.pbvenv = load_ini("main", "pbvenv")
    if ".." in st.session_state.pbvenv:
        st.session_state.pbvenv = os.path.abspath(st.session_state.pbvenv)
        save_ini("main", "pbvenv", st.session_state.pbvenv)
    pbvenv_ok = "✅" if st.session_state.pbvenv and Path(st.session_state.pbvenv).is_file() and PurePath(st.session_state.pbvenv).name.startswith("python") else "❌"

    if "input_pb7dir" in st.session_state:
        if st.session_state.input_pb7dir != st.session_state.pb7dir:
            st.session_state.pb7dir = st.session_state.input_pb7dir
            save_ini("main", "pb7dir", st.session_state.pb7dir)
            if "users" in st.session_state:
                del st.session_state.users
    st.session_state.pb7dir = load_ini("main", "pb7dir")
    if ".." in st.session_state.pb7dir:
        st.session_state.pb7dir = os.path.abspath(st.session_state.pb7dir)
        save_ini("main", "pb7dir", st.session_state.pb7dir)
    pb7dir_ok = "✅" if st.session_state.pb7dir and Path(f"{st.session_state.pb7dir}/src/passivbot.py").exists() else "❌"

    if "input_pb7venv" in st.session_state:
        if st.session_state.input_pb7venv != st.session_state.pb7venv:
            st.session_state.pb7venv = st.session_state.input_pb7venv
            save_ini("main", "pb7venv", st.session_state.pb7venv)
    st.session_state.pb7venv = load_ini("main", "pb7venv")
    if ".." in st.session_state.pb7venv:
        st.session_state.pb7venv = os.path.abspath(st.session_state.pb7venv)
        save_ini("main", "pb7venv", st.session_state.pb7venv)
    pb7venv_ok = "✅" if st.session_state.pb7venv and Path(st.session_state.pb7venv).is_file() and PurePath(st.session_state.pb7venv).name.startswith("python") else "❌"

    st.session_state.pbname = load_ini("main", "pbname")
    if not st.session_state.pbname:
        st.session_state.pbname = platform.node()
        save_ini("main", "pbname", st.session_state.pbname)

    if "role" not in st.session_state:
        st.session_state.role = load_ini("main", "role")
        if st.session_state.role == "master":
            st.session_state.master = True
        else:
            st.session_state.master = False

    # Always initialize session state objects to allow navigation
    if 'users' not in st.session_state:
        with st.spinner('Initializing Users...'):
            st.session_state.users = Users()
    if 'pbgui_instances' not in st.session_state:
        with st.spinner('Initializing Instances...'):
            st.session_state.pbgui_instances = Instances()
    if 'multi_instances' not in st.session_state:
        with st.spinner('Initializing Multi Instances...'):
            st.session_state.multi_instances = MultiInstances()
    if 'v7_instances' not in st.session_state:
        with st.spinner('Initializing v7 Instances...'):
            st.session_state.v7_instances = V7Instances()
    if 'services' not in st.session_state:
        with st.spinner('Initializing Services...'):
            st.session_state.services = Services()

    return pbdir_ok, pbvenv_ok, pb7dir_ok, pb7venv_ok

def render_welcome(pbdir_ok, pbvenv_ok, pb7dir_ok, pb7venv_ok):
    if "config_error" in st.session_state:
        st.error(st.session_state.config_error, icon="⚠️")

    col1, col2 = st.columns([5,1], vertical_alignment="bottom")
    with col1:
        st.text_input("Passivbot V6 path " + pbdir_ok, value=st.session_state.pbdir, key='input_pbdir')
    with col2:
        if st.button("Browse", key='button_change_pbdir'):
            del st.session_state.input_pbdir
            change_ini("main", "pbdir")
            if "users" in st.session_state:
                del st.session_state.users

    col1, col2 = st.columns([5,1], vertical_alignment="bottom")
    with col1:
        st.text_input("Passivbot V6 python interpreter (venv/bin/python) " + pbvenv_ok, value=st.session_state.pbvenv, key='input_pbvenv')
    with col2:
        if st.button("Browse", key='button_change_pbvenv'):
            del st.session_state.input_pbvenv
            change_ini("main", "pbvenv")

    col1, col2 = st.columns([5,1], vertical_alignment="bottom")
    with col1:
        st.text_input("Passivbot V7 path " + pb7dir_ok, value=st.session_state.pb7dir, key='input_pb7dir')
    with col2:
        if st.button("Browse", key='button_change_pb7dir'):
            del st.session_state.input_pb7dir
            change_ini("main", "pb7dir")
            if "users" in st.session_state:
                del st.session_state.users

    col1, col2 = st.columns([5,1], vertical_alignment="bottom")
    with col1:
        st.text_input("Passivbot V7 python interpreter (venv/bin/python) " + pb7venv_ok, value=st.session_state.pb7venv, key='input_pb7venv')
    with col2:
        if st.button("Browse", key='button_change_pb7venv'):
            del st.session_state.input_pb7venv
            change_ini("main", "pb7venv")

    col1, col2 = st.columns([5,1], vertical_alignment="bottom")
    with col1:
        if "input_pbname" in st.session_state:
            if st.session_state.input_pbname != st.session_state.pbname:
                st.session_state.pbname = st.session_state.input_pbname
                save_ini("main", "pbname", st.session_state.pbname)
        st.text_input("Bot Name", value=st.session_state.pbname, key="input_pbname", max_chars=32)
    with col2:
        if "input_master" in st.session_state:
            if st.session_state.input_master != st.session_state.master:
                st.session_state.master = st.session_state.input_master
                if st.session_state.master:
                    save_ini("main", "role", "master")
                    st.session_state.role = "master"
                else:
                    save_ini("main", "role", "slave")
                    st.session_state.role = "slave"
        st.checkbox("Master", value=st.session_state.master, key="input_master", help=pbgui_help.role)

    st.markdown("---")
    change_password()

# Page Setup
set_page_config("Welcome")
st.header("Welcome to Passivbot GUI", divider="red")

# Show Login-Dialog on demand
check_password()

# Once we're logged in, we can initialize the session and do checks
if is_authenticted():
    # Check if just logged in
    if "just_logged_in" not in st.session_state:
        st.session_state.just_logged_in = True
        pbdir_ok, pbvenv_ok, pb7dir_ok, pb7venv_ok = do_init()
        # Redirect to Dashboards page only after login if configuration is complete
        if is_configured():
            try:
                st.switch_page("navi/info_dashboards.py")
            except Exception as e:
                st.error(f"Cannot redirect to Dashboards: {e}. Please navigate to Dashboards manually.")
                render_welcome(pbdir_ok, pbvenv_ok, pb7dir_ok, pb7venv_ok)
        else:
            render_welcome(pbdir_ok, pbvenv_ok, pb7dir_ok, pb7venv_ok)
    else:
        # Already logged in or navigated back, show Welcome page without redirect
        pbdir_ok, pbvenv_ok, pb7dir_ok, pb7venv_ok = do_init()
        render_welcome(pbdir_ok, pbvenv_ok, pb7dir_ok, pb7venv_ok)
else:
    # Reset just_logged_in and config_error when not authenticated
    if "just_logged_in" in st.session_state:
        del st.session_state.just_logged_in
    if "config_error" in st.session_state:
        del st.session_state.config_error
