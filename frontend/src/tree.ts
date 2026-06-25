export type TreeNode = {
    name: string;
    path: string;
    directory: boolean;
    children: TreeNode[];
};

export function buildTree(items: any[]): TreeNode[] {

    const root: TreeNode[] = [];

    for (const item of items) {

        const parts = item.path.replace(/\\/g,"/").split("/");

        let current = root;
        let currentPath = "";

        for (let i=0;i<parts.length;i++) {

            const part = parts[i];

            currentPath = currentPath
                ? currentPath + "/" + part
                : part;

            let node = current.find(n=>n.name===part);

            if (!node) {

                node = {
                    name: part,
                    path: currentPath,
                    directory: i < parts.length-1 || item.directory,
                    children:[]
                };

                current.push(node);
            }

            current=node.children;
        }
    }

    return root;
}
