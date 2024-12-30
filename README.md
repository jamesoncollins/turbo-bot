# turbo-bot

you need to make a secrets.txt file that has these vairables:

export      SIGNAL_API_URL=signal-cli:8181 # URL for the signal-cli API
export      BOT_NUMBER="+1555555555" # The registered Signal number for your bot
export      CONTACT_NUMERS="+1555555555" # true/false, a single contact, a ; seperated list of contacts
export      GROUP_NAMES="MYGROUP" # true/false, a single group, a ; seperated list of groups
export      IGNORE_GROUPS="TurboBot Devel"	#optional
export      INSTA_USERNAME="myuser"
export      INSTA_PASSWORD="mypassword"
export      OPENAI_API_KEY="keygoeshere"
      
Update the docker-compose file to point the signal-cli bot(s) to your repo,
or use this one.  Default file makes one for main branch and one for devel
branch.  The run.sh script will just fail back to bash if you dont supply
a secrets.sh file in the same folder as the repo.

When you first run this you need to boot signal-cli in normal mode in order
to link it to your account.  You do that by having it generate a qr code
that you scan with your phone.  See the signalbot documentation.  tldr:
http://localhost:8181/v1/qrcodelink?device_name=local