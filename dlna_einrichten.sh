#!/bin/bash

#Konstanten definieren
dlna_dir=/media/Daten/DLNA
dlna_cache=/media/Daten/dlna_cache
baum_dir=$dlna_dir/00_Baum
liste_dir=$dlna_dir/01_Liste
musik_dir=/media/Daten/Musik
IFS=$(echo -en "\n\b")

#DLNA-Server anhalten und etwas aufräumen
systemctl stop minidlna.service
rm -rf $dlna_dir
mkdir $dlna_dir

#DLNA-Inhalte verlinken
cp -rl "$musik_dir" "$liste_dir"
mkdir "$baum_dir"
for it in "$liste_dir"/*
do
  cur_dir="$(basename "$it")"
  ln -s "$it" "$baum_dir/$cur_dir"
done

#Pseudo-BBaum bauen
(cd "$baum_dir" ; /opt/DLNA/baue_baum.py)

#Zufällige Ordner verlinken
num_rand_screens=2
num_screen_items=4
num_rand_dir=$(($num_screen_items * $num_rand_screens - 2)) # Baum und Liste abziehen
shuf_arr=($(find "$liste_dir" -iregex '.*\(ogg\|mp3\|flac\|wma\)' -exec dirname {} + | sort -u | shuf -n$num_rand_dir))
for it in $(seq 0 $(($num_rand_dir - 1)))
do
  pre_number=$(printf "%02d" $(($it + 2)))
  cur_dir="${shuf_arr[$it]}"
  album_name="$(basename "$cur_dir")"
  if echo $album_name | grep -qxiE '(CD)?[ _]?[0-9]+'
  then
    pre_dir="$(dirname "$cur_dir")"
    real_album="$(basename "$pre_dir")"
    album_name="$real_album-$album_name"
  fi
  ln -s "$cur_dir" "$dlna_dir/${pre_number}_$album_name"
done

# Berechtigungen für MiniDLNA wieder herstellen
# Eigentümer ist minidlna, aber alle dürfen Lesen und Ordner öffnen. Niemand
# darf mehr.
chown minidlna:dlnausers -R "$dlna_dir"
chown minidlna:minidlna -R "$dlna_cache"
for folder in "$dlna_dir" "$dlna_cache"
do
  find "$folder" -type f -exec chmod 660 {} +
  find "$folder" -type d -exec chmod 770 {} +
done

minidlnad -u minidlna -R -f /opt/DLNA/minidlna.conf
