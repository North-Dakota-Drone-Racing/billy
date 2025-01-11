# Billy

An unofficially supported MultiGP discord bot to promote events within a server.

Billy is meant to be connected to a running instance of Ollama to generate
unique event announcements and interactions within a discord
server using a self hosted large language model. The large language model
can be customized to the group's preference.

## Installation

Billy is installable as a pre-built docker container (preferred) or as
a standard python scipt. In both instances, the bot is configurable
by setting the following environment variables:

- `TOKEN` - The discord bot's client token.
- `OLLAMA_SERVER` - The the Ollama server's address (include http(s)://)
- `OLLAMA_PORT` - The port number of the Ollama server
- `OLLAMA_MODEL` - The name of the LLM model stored with your Ollama installation
to use.
- `BOT_NAME` - Used internally to replace the internal discord id on chat messages
before sending to ollama for response generation.

## Activating

Once the bot is in your server, it can be activated by using a `/activate` command
(this feature might take awhile to load in due to discord's bot command registration
process). This command will set the MultiGP chapter ***for the discord server***.
This allows you to use the same registered bot across multiple discord servers each
with their seperate own MultiGP chapter.

Using `/activate` will **update** the info for the current server and currently
will not allow for announcing events for multiple discord chapters in one
discord server.