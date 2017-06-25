#!/bin/bash

#Konstanten definieren
dlna_dir=/media/Daten/DLNA
liste_dir=$dlna_dir/1_Liste
musik_dir=/media/Daten/Musik
IFS=$(echo -en "\n\b")

#DLNA-Server anhalten und etwas aufräumen
/etc/init.d/minidlna stop
rm -rf $dlna_dir
mkdir $dlna_dir

#DLNA-Inhalte verlinken
cp -rl "$musik_dir" "$liste_dir"
mkdir $dlna_dir/0_Baum
for it in "$liste_dir"/*
do
  cur_dir="$(basename "$it")"
  ln -s "$it" "$dlna_dir/0_Baum/$cur_dir"
done

#Pseudo-BBaum bauen
(cd $dlna_dir/0_Baum ; /opt/DLNA/baue_baum.py)

#Zufällige Ordner verlinken
num_rand_dir=6
shuf_arr=($(find "$liste_dir" -iregex '.*\(ogg\|mp3\|flac\|wma\)' -print0 | xargs -0 dirname | sort -u | shuf -n$num_rand_dir))
for it in $(seq 0 $(($num_rand_dir - 1)))
do
  pre_number=$(($it + 2))
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

sudo minidlnad -R
sleep 3
sudo /etc/init.d/minidlna start
