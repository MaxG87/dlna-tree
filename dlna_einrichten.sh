#!/bin/bash

#Konstanten definieren
dlna_dir=/media/DLNA
musik_dir=/media/Daten/Musik
IFS=$(echo -en "\n\b")

#DLNA-Server anhalten und etwas aufräumen
/etc/init.d/minidlna stop
rm -rf $dlna_dir
mkdir $dlna_dir

#DLNA-Inhalte verlinken
ln -s $musik_dir $dlna_dir/Liste
mkdir $dlna_dir/Baum
for it in $musik_dir/*
do
  cur_dir=$(basename "$it")
  ln -s "$musik_dir/$cur_dir" "$dlna_dir/Baum/$cur_dir"
done

#Pseudo-BBaum bauen
(cd $dlna_dir/Baum ; /opt/DLNA/baue_bbaum.sh)

#Zufällige Ordner verlinken
num_rand_dir=6
shuf_arr=($(find $musik_dir -iregex '.*\(ogg\|mp3\|flac\|wma\)' -print0 | xargs -0 dirname | sort -u | shuf -n$num_rand_dir))
for it in $(seq 0 $(($num_rand_dir - 1)))
do
  cur_dir="${shuf_arr[$it]}"
  album_name="$(basename "$cur_dir")"
  if echo $album_name | grep -xiE '(CD)?[ _]?[0-9]+'
  then
    pre_dir="$(dirname "$cur_dir")"
    real_album="$(basename "$pre_dir")"
    album_name="$real_album-$album_name"
  fi
  ln -s "$cur_dir" "$dlna_dir/$album_name"
done

sudo minidlnad -R
sleep 3
sudo /etc/init.d/minidlna start
