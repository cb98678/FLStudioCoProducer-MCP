# Plugin recipes

A recipe is a named set of plugin parameters for a plugin you own. It is applied by `apply_param_recipe` using parameter names, so it survives index changes.
The agent proposes a recipe from the plugin's parameter list, you listen and approve, and it is saved here as `recipes/<name>.toml`.
Nothing is shipped: parameter names depend on the plugins on your machine.
