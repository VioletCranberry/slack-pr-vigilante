import logging
import re


class MessageElementParser:
    """ Slack Message Element Parser """

    def __init__(self, message: dict):
        self.message_timestamp = message.get("ts")
        logging.info(f"parsing [{self.message_timestamp}] "
                     f"using {self.__class__.__name__}")
        self.message = message

        self.layout_blocks = self.message.get("blocks", [])
        self.elements = self.get_layout_elements()

    def get_block_elements(self, message_block: dict, block_elements: list = None):
        block_elements = block_elements if block_elements else []

        if message_block.get("elements"):
            for block_element in message_block.get("elements"):
                if "elements" not in block_element.keys():
                    block_elements.append(block_element)
                else:
                    for element in block_element.get("elements"):
                        if "elements" not in element.keys():
                            block_elements.append(element)
                        else:
                            self.get_block_elements(element, block_elements)
        return block_elements

    def get_layout_elements(self):
        layout_elements = []
        for layout_block in self.layout_blocks:
            block_elements = self.get_block_elements(layout_block)
            layout_elements.extend(block_elements)
        logging.info(f"message [{self.message_timestamp}] contains"
                     f" {len(layout_elements)} elements")
        logging.debug(f"message layout elements: {layout_elements}")
        return layout_elements


class MessagePullRequestUrlParser(MessageElementParser):
    """ Slack Message Pull Request parser """

    def __init__(self, message: dict):
        super().__init__(message)
        logging.info(f"parsing [{self.message_timestamp}] "
                     f"using {self.__class__.__name__}")

        self.urls = [message_element.get("url") for message_element in self.elements
                     if message_element.get("type") == "link"]
        self.pull_requests = self.get_pull_requests()

    def get_pull_requests(self):
        re_pattern = r"http[s]://github.com/.+/pull/\d+"
        urls = [match.group() for url in self.urls
                if (match := re.fullmatch(re_pattern, url))]
        if urls:
            logging.info(f"message [{self.message_timestamp}] "
                         f"contains {len(urls)} pull request URLs")
            logging.debug(f"message pr urls: {urls}")
            return urls
        else:
            logging.info(f"message [{self.message_timestamp}] "
                         f"does not contain any pull requests")
            return []


class MessageReactionsParser:
    """ Slack Message Reactions Parser """

    def __init__(self, message: dict):
        self.message_timestamp = message.get("ts")
        logging.info(f"parsing [{self.message_timestamp}] "
                     f"using {self.__class__.__name__}")
        self.message = message
        self.reactions = self.get_message_reactions()

    def get_message_reactions(self):
        reactions = self.message.get("reactions", [])
        reaction_names = [reaction.get("name") for reaction in reactions]
        reactions_count = len(reaction_names)

        if reactions_count > 0:
            logging.info(f"message [{self.message_timestamp}] "
                         f"contains {reactions_count} reactions")
            logging.debug(f"message reactions: {reaction_names}")
        else:
            logging.info(f"message [{self.message_timestamp}]"
                         f" has no user reactions")

        return reaction_names

    def lookup_reaction(self, reaction):
        if reaction in self.reactions:
            logging.info(f"message [{self.message_timestamp}]: "
                         f"reaction {reaction} was found")
            return True
        else:
            logging.info(f"message [{self.message_timestamp}]: "
                         f"reaction {reaction} was not found")
            return False
