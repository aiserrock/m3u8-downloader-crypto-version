## For run need find two links:  
Step 1 --- link with key like this:  `https://play.boomstream.com/api/process/241d2712370f383c325e07570e0367250720112950465c0055555269575a053e5a5b075a5d593e010d533b`.   
  This link need paste into method named run (140 line `key_url`). 

Step 2 --- `chunklist.m3u8`. 
The contents of the file must be put in a file named `playlist.txt`

After this run it: `python3 boomstream.py`




The script downloads videos from boomstream.com streaming service.

## Encryption algorithm description

The service stores video chunks encrypted using HLS AES-128 algorithm. In order to decrypt
them AES initialization vector and 128-bit key are required. Initialization vector is encrypted
in the first part of `#EXT-X-MEDIA-READY` variable which is contained in m3u8 playlist using a
simple XOR operation. The key is supposed to be recevied via HTTP using a URL that starts with
`https://play.boomstream.com/api/process/` and contains a long hex key that can be computed
using session token and the second part of `#EXT-X-MEDIA-READY`.

## Usage

Spicify `--url` and `--pin` in command line arguments:

```bash
https://play.boomstream.com/TiAR7aDs?ppv=EswAWlFa --pin 123-456-789
```

You can also specify a resolution using `--resolution` command line argument:

```bash
https://play.boomstream.com/TiAR7aDs?ppv=EswAWlFa --pin 123-456-789 --resolution "640x360"
```

If resolution is not specified, the video with a highest one will be dowloaded.

## Requirements

* openssl
* curl
* python-requests
* lxml
* ffmpeg (for enconding ts -> mp4)

As the script was written and tested in Linux (specifically Ubuntu 18.04.4 LTS) it uses GNU/Linux
`cat` tool to merge the video pieces into one single file. I think this is the only thing that prevents
it from running in Windows. If you have time to make a PR to fix that I will really appreciate.
