import os

def setup_sdk():
    base_dir = os.path.dirname(os.path.abspath(__file__))

    # Path to arena_sdk folder
    sdk_root = os.path.join(base_dir, "arena_sdk")

    # Correct folders for Python
    sdk_lib = os.path.join(sdk_root, "lib64")
    sdk_genicam_bin = os.path.join(sdk_root, "GenICam", "bin", "Win64_x64")

    # Add DLL path
    os.environ["PATH"] = sdk_lib + ";" + os.environ.get("PATH", "")

    # Set GenTL path (IMPORTANT)
    os.environ["GENICAM_GENTL64_PATH"] = sdk_genicam_bin

    # print("Arena SDK environment configured.")