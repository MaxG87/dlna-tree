#!/bin/bash

set -euo pipefail

function user_from_dir() {
    dir="$1"
    stat -c %u "$dir"
}

function get_n_random_music_folders() {
    local num_rand_dir="$1"
    local ignorelist='Hörbücher|Kinder-|Känguru'
    find "$liste_dir" -iregex '.*\(ogg\|mp3\|flac\|wma\)' -exec dirname {} + |
    grep -vE "$ignorelist" |
    sort -u |
    shuf -n"$num_rand_dir"

}

#Konstanten definieren
dlna_dir=/media/Daten/DLNA
baum_dir=$dlna_dir/00_Baum
liste_dir=$dlna_dir/01_Liste
musik_dir=/media/Daten/Musik
musik_dir_owner="${USER:-$(user_from_dir "$musik_dir")}"
IFS=$(echo -en "\n\b")

#DLNA-Server anhalten und etwas aufräumen
service minidlna stop
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
num_rand_dir=$((num_screen_items * num_rand_screens - 2)) # Baum und Liste abziehen
readarray -t random_music_selection<<<"$(
    get_n_random_music_folders "$num_rand_dir"
)"
for ((it=0; it<num_rand_dir; it++))
do
  pre_number=$(printf "%02d" $((it + 2)))
  cur_dir="${random_music_selection[$it]}"
  album_name="$(basename "$cur_dir")"
  if echo "$album_name" | grep -qxiE '(CD)?[ _]?[0-9]+'
  then
    pre_dir="$(dirname "$cur_dir")"
    real_album="$(basename "$pre_dir")"
    album_name="$real_album-$album_name"
  fi
  ln -s "$cur_dir" "$dlna_dir/${pre_number}_$album_name"
done

chown "$musik_dir_owner":dlnausers -R "$musik_dir"
chown minidlna:minidlna -R "$dlna_dir"
service minidlna start
