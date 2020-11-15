mkdir -p ~/.ansible/plugins/inventory
mkdir -p ~/.ansible/plugins/modules
mkdir -p ~/.ansible/plugins/action

CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"


for action_plugin in "$CURRENT_DIR/action_plugins"/*.py
do
  echo "Create symlink: $action_plugin --> ~/.ansible/plugins/action/$(basename $action_plugin)"
  ln -sf $action_plugin ~/.ansible/plugins/action/$(basename $action_plugin)
done

for module in "$CURRENT_DIR/modules"/*.py
do
  echo "Create symlink: $module --> ~/.ansible/plugins/modules/$(basename $module)"
  ln -sf $module ~/.ansible/plugins/modules/$(basename $module)
done

for inventory in "$CURRENT_DIR/inventory_plugins"/*.py
do
  echo "Create symlink: $inventory --> ~/.ansible/plugins/inventory/$(basename $inventory)"
  ln -sf $inventory ~/.ansible/plugins/inventory/$(basename $inventory)
done
