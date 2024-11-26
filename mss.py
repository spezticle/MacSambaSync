import os
import yaml
import subprocess


def load_config(file_path="config.yaml"):
    """
    Load configuration from a YAML file.
    """
    try:
        with open(file_path, "r") as f:
            config = yaml.safe_load(f)
        print("Configuration loaded successfully.")
        return config
    except FileNotFoundError:
        print(f"Error: {file_path} not found.")
        exit(1)
    except yaml.YAMLError as e:
        print(f"Error parsing YAML: {e}")
        exit(1)


def is_mounted(target):
    """
    Check if the target (mount point or share) is already mounted.
    """
    try:
        mount_output = subprocess.check_output(["mount"], text=True)
        for line in mount_output.splitlines():
            if target in line:
                return True
    except subprocess.CalledProcessError as e:
        print(f"Error checking mounts: {e}")
        exit(1)
    return False


def ensure_mount_directory(mount_path):
    """
    Ensure the specified mount directory exists with appropriate permissions.
    If it doesn't exist, use sudo to create and assign permissions to the user.
    """
    if not os.path.exists(mount_path):
        print(f"Creating mount directory: {mount_path}")
        try:
            # Create the directory with sudo
            subprocess.run(["sudo", "mkdir", "-p", mount_path], check=True)
            # Assign ownership to the current user and their primary group
            user = os.getenv("USER")
            group = subprocess.check_output(["id", "-gn"], text=True).strip()
            subprocess.run(["sudo", "chown", f"{user}:{group}", mount_path], check=True)
            print(f"Successfully created and assigned permissions for {mount_path}")
        except subprocess.CalledProcessError as e:
            print(f"Error creating or assigning permissions for {mount_path}: {e}")
            exit(1)
    else:
        print(f"Mount directory already exists: {mount_path}")


def mount_smb(share):
    """
    Mount an SMB share dynamically or under a specified mount_base.
    """
    if 'mount_point' in share:
        # If a specific mount point is defined, ensure the directory exists
        mount_point = os.path.join("/Volumes", share['mount_point'])
        if is_mounted(mount_point):
            print(f"SMB share {share['name']} is already mounted at {mount_point}. Skipping.")
            return
        ensure_mount_directory(mount_point)
        print(f"Mounting SMB share: {share['name']} -> {mount_point}")
        options = share.get("options", "")
        command = [
            "mount",
            "-t", "smbfs",
            f"//{share['username']}:{share['password']}@{share['host']}{share['path']}",
            mount_point
        ]
    else:
        # Use the `open` command for dynamic mounting
        share_url = f"smb://{share['username']}:{share['password']}@{share['host']}{share['path']}"
        if is_mounted(share_url):
            print(f"SMB share {share['name']} is already mounted dynamically. Skipping.")
            return
        print(f"Mounting SMB share dynamically: {share['name']} (macOS will assign a mount point)")
        command = ["open", share_url]

    try:
        subprocess.run(command, check=True)
        print(f"Successfully mounted SMB share: {share['name']}")
    except subprocess.CalledProcessError as e:
        print(f"Error mounting SMB share {share['name']}: {e}")


def mount_nfs(share):
    """
    Mount an NFS share under the specified mount_base.
    """
    mount_point = os.path.join("/Volumes", share['mount_point'])
    if is_mounted(mount_point):
        print(f"NFS share {share['name']} is already mounted at {mount_point}. Skipping.")
        return
    ensure_mount_directory(mount_point)
    print(f"Mounting NFS share: {share['name']} -> {mount_point}")

    # Build the NFS mount command
    options = share.get("options", "")
    command = [
        "mount",
        "-t", "nfs",
        f"{share['host']}:{share['path']}",
        mount_point
    ]

    if options:
        command.append("-o")
        command.append(options)

    try:
        subprocess.run(command, check=True)
        print(f"Successfully mounted NFS share: {share['name']}")
    except subprocess.CalledProcessError as e:
        print(f"Error mounting NFS share {share['name']}: {e}")


def main():
    """
    Main function to load configuration and mount shares.
    """
    config = load_config()  # Load config.yaml
    smb_shares = config.get("mounts", {}).get("smb", [])
    nfs_shares = config.get("mounts", {}).get("nfs", [])

    # Process SMB shares
    if smb_shares:
        print("Processing SMB shares...")
        for smb in smb_shares:
            mount_smb(smb)

    # Process NFS shares
    if nfs_shares:
        print("Processing NFS shares...")
        for nfs in nfs_shares:
            mount_nfs(nfs)


if __name__ == "__main__":
    main()