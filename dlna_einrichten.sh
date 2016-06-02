#!/bin/bash

#Konstanten definieren
dlna_dir=/media/DLNA
musik_dir=/media/Daten/Musik

#DLNA-Server anhalten und etwas aufräumen
/etc/init.d/minidlna stop
rm -rf $dlna_dir
mkdir $dlna_dir

#DLNA-Inhalte verlinken
ln -s $musik_dir $dlna_dir/Liste
mkdir $dlna_dir/Baum
IFS_ALT=$IFS
IFS=$(echo -en "\n\b")
for it in $musik_dir/*
do
  cur_dir=$(basename "$it")
  ln -s "$musik_dir/$cur_dir" "$dlna_dir/Baum/$cur_dir"
done
IFS=$IFS_ALT

#Pseudo-BBaum bauen
(cd $dlna_dir/Baum ; /home/olimex/baue_bbaum.sh)

#Zufällige Ordner verlinken
num_rand_dir=3
shuf_arr=($(find $musik_dir -iregex '.*\(ogg\|mp3\|flac\|wma\)' -exec dirname {} \+ | sort -u | shuf -n$num_rand_dir))
for it in $(seq 0 $(($num_rand_dir - 1)))
do
  ln -s "${shuf_arr[$it]}" "$dlna_dir/Zufall_$(($it + 1))"
done

sudo minidlnad -R
sleep 3
sudo /etc/init.d/minidlna start
