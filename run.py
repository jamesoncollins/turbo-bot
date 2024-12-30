import os
import sys
from signalbot import SignalBot, Command, Context
import re
import time
import base64
from handlers.base_handler import BaseHandler
from utils import *
import time

start_time = time.time()

LOGMSG = "----TURBOBOT----\n"

import git
import os

def get_git_info():
    """
    Retrieves the current branch name and commit ID of the Git repository.

    Returns:
        tuple: A tuple containing the branch name and commit ID.
               Returns (None, None) if not in a Git repository.
    """
    try:
        repo = git.Repo(os.path.dirname(os.path.abspath(__file__)), search_parent_directories=True)
        branch_name = repo.active_branch.name
        commit_id = repo.head.commit.hexsha
        return branch_name, commit_id
    except git.InvalidGitRepositoryError:
        return None, None

def find_group_by_internal_id(data, target_id):
    for entry in data:
        if entry['internal_id'] == target_id:
            #return entry['name']
            return entry
    return None

# this is a copy of signalbot's reply function.
# im going to try and make a version that replies to the other particiapnt in
# a 1 on 1 chat even if i was the original sender.
async def reply(
    c,
    text: str,
    base64_attachments: list = [],
    mentions: list = None,
    text_mode: str = None,
):

    source = c.message.source
    desintation = c.message.raw_message["envelope"]["syncMessage"]["sentMessage"]["destination"]
  
    #fixme: dont use OS var here, get it from the bot
    if c.message.group or source != os.environ["BOT_NUMBER"]:
        # this was a group message
        # do a normal reply
        return await c.reply(str, base64_attachments)    
    else:
        # this was a 1on1 message that we send ourselves    
        return await c.bot.send(
            desintation,
            text,
            base64_attachments=base64_attachments,
            quote_author=c.message.source,
            quote_mentions=c.message.mentions,
            quote_message=c.message.text,
            quote_timestamp=c.message.timestamp,
            mentions=mentions,
            text_mode=text_mode,
            )

class PingCommand(Command):
    async def handle(self, c: Context):

        # this will go away once signalbot is fixed
        # Parse environment variables
        contact_numbers = parse_env_var("CONTACT_NUMBERS")
        group_names = parse_env_var("GROUP_NAMES")
        ignore_groups = parse_env_var("IGNORE_GROUPS")

        #
        # WARNING: Seems that iPhones might not report their phone
        # number and isntead youll get the UUID
        #
        # for future reference, here is some info you can get
        # note that c.message
        msg = c.message.text        # the text of the message
        group = c.message.group     # some kind of group ID
        source = c.message.source                   # a phone number
        source_number = c.message.source_number     # same as above
        source_uuid = c.message.source_uuid
        b64_attachments = c.message.base64_attachments        
        source_name = c.message.raw_message["envelope"]["sourceName"]   # this is a display name, i.e. Bob Smith
        
        # was this a 1on1 message, or a group message?
        if c.message.group == None:
            # this is not a group message
            # see what the destination is
            desintation = c.message.raw_message["envelope"]["syncMessage"]["sentMessage"]["destination"]
            desintation_uuid = c.message.raw_message["envelope"]["syncMessage"]["sentMessage"]["destinationUuid"]
        else:               
            # the message contains the group ID, but not the group name.
            # the bot knows all the group names and IDs that the BOT_NUMBER has
            # this try-except is just for unittests, becuase it doesn't populate these
            # fields correctly
            try:
                group = find_group_by_internal_id(c.bot.groups, c.message.group)
                group_name = group["name"]
                if ignore_groups and group_name in ignore_groups:
                    print("Ignored group")
                    return
                if group_name not in group_names and group_names != True:
                    print("group not in group list or group_names isnt True")
                    return
            except Exception as e:
                print(f"Failed to get group info: {e}")

        

        if msg is None:
            print("Message was None")
        elif msg == "Ping":
            print("is ping")
            await c.reply(  LOGMSG + "Pong")
        elif (url := is_reddit_domain(msg)):
            print("is reddit url")
            video_b64 = download_reddit_video_tryall_b64(url)            
            if (video_b64):
                await c.reply(  LOGMSG + "Reddit URL: " + url, base64_attachments=[video_b64])
        elif "instagram.com" in msg:
            print("is insta")
            url = extract_url(msg, "instagram.com")
            video_b64 = download_instagram_video_as_b64(url)
            await c.reply(  LOGMSG + "IntsgramURL: " + url, base64_attachments=[video_b64])  
        elif (tickers := extract_ticker_symbols(msg)):
            print("is ticker")
            plot_b64 = plot_stock_data_base64(tickers)
            summary = get_stock_summary( convert_to_get_stock_summary_input(tickers) )
            await c.reply(  LOGMSG + summary, base64_attachments=[plot_b64])  
        elif msg == "#":
            print("is hash")
            branch, commit = get_git_info()
            str = f"Uptime: {(time.time() - start_time)} seconds\n"
            if branch and commit:
                str += f"Branch: {branch}\n"
                str += f"Commit ID: {commit}\n"
            else:
                str += "Not in a Git repository."
            await c.reply(  LOGMSG + "I am here.\n" + str)            
        elif msg == "#turboboot":
            print("is reboot")
            await c.reply(  LOGMSG + "turbobot rebooting...")
            sys.exit(1)
        else:
            handler_classes = BaseHandler.get_all_handlers()
            for handler_class in handler_classes:
                try:
                    handler_name = handler_class.get_name()
                    handler = handler_class(msg)
                    handler.assign_context(c)
                    if handler.can_handle():
                        print("Handler Used:", handler_class.get_name())
                        await c.reply(  LOGMSG + handler.get_message(), base64_attachments=handler.get_attachments() ) 
                        #return
                except Exception as e:
                    print(f"Handler {handler_name} exception: {e}")
        return


def parse_env_var(env_var, delimiter=";"):
    """
    Parses an environment variable and returns a list, a boolean, or None.
    
    Args:
        env_var (str): The name of the environment variable.
        delimiter (str): The delimiter used for splitting lists.
        
    Returns:
        list, bool, or None: Parsed value from the environment variable.
    """
    value = os.environ.get(env_var, None)
    if value is None or value.strip() == "":
        return None  # Treat as "not supplied"
    
    #value = value.strip().lower()
    
    if value in {"true", "false"}:
        return value == "true"  # Return as a Python boolean
    elif delimiter in value:
        return value.split(delimiter)  # Return as a list
    else:
        return [value]  # Single value as a list


if __name__ == "__main__":
    bot = SignalBot({
        "signal_service": os.environ["SIGNAL_API_URL"],
        "phone_number": os.environ["BOT_NUMBER"]
    })

    print('bot starting...')

    # Parse environment variables
    contact_number = parse_env_var("CONTACT_NUMBERS")
    group_name = parse_env_var("GROUP_NAMES")
    ignored_groups = parse_env_var("IGNORED_GROUPS")
    print(f"conacts {contact_number}, groups {group_name}, ignored groups {IGNORED_GROUPS}")
    
    # Determine behavior based on parsed variables
    
    # if neither var was supplied, then listen to everything

    if contact_number is None and group_name is None:
        # Register for all contacts and groups
        print("registering bot for all contacts and groups")
        bot.register(PingCommand())
    elif contact_number is None or group_name is None:
        print("Must define contact and group, one may just be true or false")
        sys.exit(1)
    else:
        # they were either true/false, a single element, or a list
        
        #
        # FIXME: As of this current signal bot version the group name function is broken.
        # Instead, always set groups to either True or false and manually parse them in 
        # our main loop.
        if group_name:
            group_name = True
        else:
            group_name = False
            
        bot.register(PingCommand(), contacts=contact_number, groups=group_name)
        
    bot.start()
    
    
    
