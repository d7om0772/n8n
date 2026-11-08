set -e
X() { # name src start dur vf
  mkdir -p frames/clips/$1; rm -f frames/clips/$1/*.jpg
  ffmpeg -v error -y -ss $3 -t $4 -i footage/hd_$2.mp4 -vf "$5,fps=30" -q:v 3 frames/clips/$1/%04d.jpg
  echo "$1 $(ls frames/clips/$1 | wc -l)"
}
X hook 34289018 0.3 3.2 "scale=1080:1920"
X rtx 5467289 3 4.5 "scale=1232:693,crop=940:693"
X gpu2 5466792 2 3 "scale=1232:693,crop=940:693"
X ready1 30518577 0.5 4.5 "crop=1300:1080:420:0,scale=420:349"
X ready2 34821018 0.2 4.5 "crop=1300:1080:300:0,scale=420:349"
X ready3 3147349 2 4.5 "crop=1300:1080:300:0,scale=420:349"
X ram 10470834 1 4 "scale=1080:1920"
X board 6754834 16 5.2 "scale=1956:1100,crop=960:1100:600:0"
X endpc 34280528 0 5 "setpts=1.1*PTS,scale=1080:1920"
