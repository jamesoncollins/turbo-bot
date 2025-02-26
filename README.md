# turbo-bot

## How this works

A docker compose file is used to run a signalbot, and the signal rest api.

The signalbot docker will automatically get this repo and execute run.py.


## Running

Execute the docker compose file.  In the signalbot docker make sure you make a secrets.txt file that has these vairables:

```
export      SIGNAL_API_URL=signal-cli:8181 # URL for the signal-cli API
export      BOT_NUMBER="+1555555555" # The registered Signal number for your bot
export      CONTACT_NUMERS="+1555555555" # true/false, a single contact, a ; seperated list of contacts
export      GROUP_NAMES="MYGROUP" # true/false, a single group, a ; seperated list of groups
export      IGNORE_GROUPS="TurboBot Devel"	#optional
export      INSTA_USERNAME="myuser"
export      INSTA_PASSWORD="mypassword"
export      OPENAI_API_KEY="keygoeshere"
```
      
Update the docker-compose file to point the signal-cli bot(s) to your repo,
or use this one.  Default file makes one for main branch and one for devel
branch.  The run.sh script will just fail back to bash if you dont supply
a secrets.sh file in the same folder as the repo.

When you first run this you need to boot signal-cli in normal mode in order
to link it to your account.  You do that by having it generate a qr code
that you scan with your phone.  See the signalbot documentation.  tldr:
http://localhost:8181/v1/qrcodelink?device_name=local


Manually running signal-cli from command line.  Be sure to stop the instance
first:

```
docker run --env "MODE=json-rpc" --env "PORT=8181" --env "PATH=/usr/local/sbin:/usr/local/bin:/usr/sbin:/usr/bin:/sbin:/bin" --env "GIN_MODE=release" --env "BUILD_VERSION=0.90" --env "SIGNAL_CLI_CONFIG_DIR=/home/.local/share/signal-cli" --env "SIGNAL_CLI_UID=1000" --env "SIGNAL_CLI_GID=1000" --entrypoint "/entrypoint.sh" --volume "/share/CACHEDEV1_DATA/Container/container-station-data/lib/docker/volumes/app-1_signal-cli-data/_data:/home/.local/share/signal-cli"  bbernhard/signal-cli-rest-api:latest
```

This was generated with:

```
container_id="signal-cli"
docker inspect $container_id | jq -r '
  .[] | 
  "docker run " +
  (if .Config.Env then (.Config.Env | map("--env \"" + . + "\"") | join(" ")) else "" end) + " " +
  (if .Config.Entrypoint then "--entrypoint \"" + (.Config.Entrypoint | join(" ")) + "\" " else "" end) +
  (if .Mounts then (.Mounts | map("--volume \"" + .Source + ":" + .Destination + "\"") | join(" ")) else "" end) + " " +
  (if .Config.Cmd then (.Config.Cmd | join(" ")) else "" end) +
  " " + .Config.Image
'
```


# Development

You can develop in windows, linux, wsl, and mac all relatively easily.

For Windows I'd suggest using miniconda.

Running the tests on your own windows or linux box is pretty easy.

If on windows just install miniconda and then run `pip3 install -r requirements.txt`.

Then you can run all the tests with `python3 -m unittest discover -s tests -p "test_*.py"`

You can also do it in WSL 1 or 2.

Some handlers might also require apt-get packages.  i.e. ffmpeg.  You can get 
ffmpeg in miniconda (i.e. conda install ffmpeg) or wsl (via apt-get or whatever).



