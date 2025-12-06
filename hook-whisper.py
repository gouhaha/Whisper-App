from PyInstaller.utils.hooks import collect_data_files
# include every file under whisper/assets  (npz, jit, etc.)
datas = collect_data_files("whisper", includes=["assets/*"])

