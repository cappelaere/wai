# TODO

- Move code to "processor" folder.
- Optimize code to extract text.  Parser should only be instantiated once.
- Use multiple workers to process applications.
- Ask for other optimization options
- Create "copilot" folder to store the copilot AI assistant using multiple agents.
- Create Web server to host user interface to display results and host the AI Copilot
- GITHUB repo
- Create PROMPT_OUTPUT_DIR and /{model} to store model prompts

# DONE
- Create LOG_OUTPUT_DIR env and append summaries to output.log
- Keep track of elapsed time to process the steps and display it in summary.
- Limit argument should be set to 0 by default to mean to process all applications for all steps
- Create SCHEMA_OUTPUT_DIR env set to "schemas" to store output schemas of all models
- Create a step 5 for scholarship statistics