# Tested on Python 3.11.11 (known not to work on 3.12 and up)

Set-Location -Path "C:\Users\Admin\Documents\work\projects\VSCodeProjects\MultiLoad"

conda activate

conda activate "C:\Users\Admin\Documents\work\projects\VSCodeProjects\MultiLoad\.conda"

black MultiLoad.py

nuitka --onefile --standalone --windows-console-mode=disable --file-version=0.1.0.0 --product-version=0.1.0.0 --file-description="MultiLoad" --product-name="MultiLoad" --copyright="© 2025 Flaming Water" --windows-icon-from-ico="C:\Users\Admin\Documents\work\projects\VSCodeProjects\MultiLoad\docs\icon.ico" --include-module=win32gui --include-module=win32api --include-data-dir="C:\Users\Admin\Documents\work\projects\VSCodeProjects\MultiLoad\docs=docs" --output-dir="C:\Users\Admin\Documents\work\projects\VSCodeProjects\MultiLoad\main" --enable-plugin=upx --upx-binary="C:\Users\Admin\Documents\work\projects\upx-4.2.4-win64\upx-4.2.4-win64" --lto=yes --clang --remove-output MultiLoad.py

Start-Sleep -Seconds 3