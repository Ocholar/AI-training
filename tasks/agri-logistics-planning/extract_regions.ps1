$csvPath = 'c:\Users\Administrator\Documents\Agricultural Productivity Analysis for African Food Security Policy\Cleaned_Datasets\cleaned_lsms_cropcut.csv'
$data = Import-Csv $csvPath | Where-Object { $_.Crop -eq 'Maize' }
$uniqueRegions = $data | Select-Object -Property Country, L0_GID, L1_GID, L2_GID, Yield_ton_ha_ -Unique | Select-Object -First 50
$uniqueRegions | ConvertTo-Json
