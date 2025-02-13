bl_info = {
    "name": "K3D Asset Collection Maker",
    "author": "MassieVFX",
    "version": (1, 2),
    "blender": (2, 80, 0),
    "location": "View3D > Object > KitBash3D - Make Asset Collection",
    "description": "Make asset collection from a KitBash3D Blender file",
    "warning": "",
    "doc_url": "",
    "category": "Object",
}

import bpy

def k3d_asset_col_menuFn(self, context):
    # This function defines the menu layout
    self.layout.separator()
    self.layout.operator("object.k3d_asset_col_operator")

class OBJECT_OT_K3D_make_asset_col(bpy.types.Operator):
    # Operator definition
    bl_idname = "object.k3d_asset_col_operator"
    bl_label = "KitBash3D - Make Asset Collection"

    def execute(self, context):
        # Define the action to be executed when the menu item is clicked
    
        # Open your KB3D Pack. Make sure the textures are loaded and everything works as intended. This script assumes the Scene is named KB3D_"TitleCasePackName"-Native. It should be that by default.
        # Create a new folder in your Asset Library Folder for Blender. (Edit>Preferences>FilePaths>AssetLibraries). I recommend a setup like this 
        # (D:/BlenderAssetLibraries/KB3D/CyberDistricts/Cyberdistricts.blend)
        # Where "CyberDistricts" would be the AssetLibrary.
        # Open the script in Blender by going to the Text Editor and clicking "Open" to locate the file, or paste it from the Gist.
        # Run the script by clicking the "Run Script" button in the Text Editor or pressing Alt+P.
        # The script will create new collections for each type of asset in your scene and move the assets into these collections. It will also generate a unique ID for the asset pack and each asset in the pack.
        # The script will then update the asset catalog file to include the new asset pack and each asset in the pack.
        # Once the script is finished, you can save your Blender file and close it.
        # You should now see it in the asset libraries section on Blender.
        # Troubleshooting: If something goes wrong or a mistake is maid I have minimal errorchecking. Just undo before the script was run and delete the Catalogs or the "blender_assets.cats.txt" file, 
        # they may trip up the script if it failed partway through.
        # I put a lot of effort into making this, so if you'd like to show your appreciation-
        #   you can donate to me through PayPal at the link below: https://paypal.me/mintyfresh

        # Update: Remade better.
        # TODO: Add simple GUI, test all packs, ensure consistent sizing and proper integration for easy placing of props.

        import os
        from pathlib import Path
        import uuid

        #filename
        file_name = str(bpy.data.scenes.keys()[0].split('_')[1].split('-')[0])
        folder = Path(bpy.data.filepath).parent
        new_uuid = str(uuid.uuid4())

        # Mapping for collections to asset types

        collection_map = {
            "Props": "Prop",
            "Buildings": "Bldg",
            "Structures": "Strc",
            "Vehicles": "Vehi",
            "Creatures": "Crea"
        }

        kit_catalog = {}

        flipped_cmap = {v: k for k, v in collection_map.items()}

        # Create the primary collections
        primary_collections = ["Props", "Buildings", "Structures", "Vehicles", "Creatures", "Other"]
        for collection_name in primary_collections:
            new_collection = bpy.data.collections.new(collection_name)
            bpy.context.scene.collection.children.link(new_collection)

        # Loop through all the empties and sort them into the collections for the library
        for obj in bpy.data.objects:
            if obj.type == "EMPTY" and obj.name.startswith("KB3D_"):

                # Sort the new collection into the correct group
                asset_type = obj.name.split("_")[2][:4]

                # Check if the asset_type exists in the flipped_cmap dictionary
                if asset_type in flipped_cmap:
                    cm_col_name = flipped_cmap[asset_type]
                else:
                    cm_col_name = "Other"

                # Create a new collection with Empty's name
                new_collection = bpy.data.collections.new(obj.name)
                bpy.data.collections[obj.name].objects.link(obj)

                # Linking Object groups
                cm_col = bpy.data.collections[cm_col_name]
                # Move the object's children to the new collection
                bpy.data.collections[cm_col.name].children.link(bpy.data.collections[obj.name])
                kit_catalog[obj.name] = cm_col.name
                
        print(kit_catalog.values())

        # Loop over Object and relink to parents.
        for obj in bpy.data.objects:
            if obj.type == "MESH" and obj.parent != None:
                bpy.data.collections[obj.parent.name].objects.link(obj)
                
        for empty in bpy.data.objects:
            if empty.type == 'EMPTY' and empty.name.startswith('KB3D_'):
                bpy.context.scene.collection.objects.unlink(empty)
                for child in empty.children:
                    bpy.context.scene.collection.objects.unlink(child)

        for col in bpy.data.collections:
            if col.name.startswith('KB3D_'):
                col.asset_mark()

        # Create a list of all empty objects
        empty_objects = [obj for obj in bpy.data.objects if obj.type == "EMPTY" and obj.name.startswith("KB3D_")]

        # Loop through the list of empty objects and clear their locations
        for obj in empty_objects:
            obj.location = (0, 0, 0)

        asset_catalog_path = folder / "blender_assets.cats.txt"

        # Initialize the list of lines and the asset_uuids dictionary
        lines = []
        asset_uuids = {}

        # Read the existing asset catalog file into a list of lines
        with asset_catalog_path.open('a+') as f:
            f.seek(0)  # Move the file pointer to the beginning of the file
            lines = f.readlines()

        # Check if the blender_assets.cats.txt file is empty and initialize it if necessary
        if os.path.getsize(asset_catalog_path) == 0:
            header_lines = [
                "# This is an Asset Catalog Definition file for Blender.\n",
                "#\n",
                "# Empty lines and lines starting with `#` will be ignored.\n",
                "# The first non-ignored line should be the version indicator.\n",
                "# Other lines are of the format \"UUID:catalog/path/for/assets:simple catalog name\"\n",
                "\n",
                "VERSION 1\n\n"
            ]
            lines.extend(header_lines)

        # Add new lines to the catalog if necessary
        file_contents = ''.join(lines)




        # Initialize the asset_uuids dictionary outside the condition
        collection_uuids = {collection_name: [] for collection_name in collection_map.keys()}
        collection_uuids["Other"] = []

        if file_name not in file_contents:
            if "KB3D" not in file_contents:
                lines.append(f"{str(uuid.uuid4())}:KB3D:KB3D\n")
            lines.append(f"{str(uuid.uuid4())}:KB3D/{file_name}:{file_name}\n")

            for collection_name in collection_map.keys():
                asset_uuid = str(uuid.uuid4())
                asset_uuids[collection_name] = asset_uuid
                lines.append(f"{asset_uuid}:KB3D/{file_name}/{collection_name}:{collection_name}\n")

            asset_uuid = str(uuid.uuid4())
            asset_uuids["Other"] = asset_uuid
            lines.append(f"{asset_uuid}:KB3D/{file_name}/Other:Other\n")

        # Write the updated list of lines back to the file
        with asset_catalog_path.open("w") as f:
            f.writelines(lines)

        kit_catalog = {}

        # delete all empties
        bpy.ops.object.select_by_type(type='EMPTY')
        bpy.ops.object.delete(use_global=False, confirm=False)

        # Asset Library Adder
        for col in bpy.data.collections:
            try:
                if col.name.startswith("KB3D_"):
                    # Gets the asset type of an object from the Name
                    # Ex: Bldg Prop Strc
                    asset_type = col.name.split("_")[2][:4]  # e.g. "Bldg"

                    # Check if the asset_type exists in the flipped_cmap dictionary
                    if asset_type in flipped_cmap:
                        asset_name = flipped_cmap[asset_type]  # e.g. "Buildings"
                        col.asset_data.catalog_id = asset_uuids[asset_name]
                    else:
                        asset_name = "Other"
                        col.asset_data.catalog_id = asset_uuids[asset_name]  # Set the catalog_id for the "Other" category

                    print(col.name, asset_name)
                    # Linking Object groups
                    cm_col = bpy.data.collections[col.name]  # Buildings [Collection]
                    print('adding', col.name, 'asset_data')# This function will be called when the menu item is clicked
            except Exception as eee:
                self.report({'INFO'}, 'Cannot Find Key: '+str(eee))

        # Force refresh add asset
        for col in bpy.data.collections:
            if col.name.startswith("KB3D_"):
                col.asset_clear()
                col.asset_mark()

        return {'FINISHED'}

def register():
    bpy.utils.register_class(OBJECT_OT_K3D_make_asset_col)
    bpy.types.VIEW3D_MT_object.append(k3d_asset_col_menuFn)

def unregister():
    bpy.utils.unregister_class(OBJECT_OT_K3D_make_asset_col)
    bpy.types.VIEW3D_MT_object.remove(k3d_asset_col_menuFn)
