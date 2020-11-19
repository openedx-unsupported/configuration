.PHONY: help build clean publish

IMAGES:=\
	build/edxapp \
    build/elasticsearch \
    build/forum \
    build/mongo \
    build/mysql \
    build/nginx

# Terminal coloring
RED:=$$(tput setaf 1)
GREEN:=$$(tput setaf 2)
BLUE:=$$(tput setaf 4)
CLEAR:=$$(tput sgr 0)
BOLD:=$$(tput bold)

help:
	@echo "$(BOLD)Global commands:$(CLEAR)$(NORMAL)"
	@echo "  $(BOLD)$(GREEN)help$(CLEAR)    Display this menu."
	@echo
	@echo "$(BOLD)Workstation image commands:$(CLEAR)$(NORMAL)"
	@echo "  $(BOLD)$(GREEN)build$(CLEAR)      Build images."
	@echo "  $(BOLD)$(GREEN)clean$(CLEAR)      Delete local images."
	@echo "  $(BOLD)$(GREEN)publish$(CLEAR)    Push all images to registry."
	@echo

## Workstation image commands
build:
	@$(patsubst %,make -C % build;, $(IMAGES))

clean:
	@$(patsubst %,make -C % clean;, $(IMAGES))

publish:
	@echo "$(BOLD)$(GREEN)Publishing images...$(CLEAR)"
	@$(patsubst %,make -C % publish;, $(IMAGES))
