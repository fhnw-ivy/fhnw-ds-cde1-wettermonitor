year=$(date +%Y)

wget https://data.stadt-zuerich.ch/dataset/sid_wapo_wetterstationen/download/messwerte_mythenquai_$year.csv
wget https://data.stadt-zuerich.ch/dataset/sid_wapo_wetterstationen/download/messwerte_tiefenbrunnen_$year.csv

mkdir -p ./csv/

mv messwerte_mythenquai_$year.csv ./csv/messwerte_mythenquai.csv
mv messwerte_tiefenbrunnen_$year.csv ./csv/messwerte_tiefenbrunnen.csv