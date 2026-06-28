export type TreeNode = {
    name: string;
    path: string;
    directory: boolean;
    children: TreeNode[];
};

type TreeItem = string | { path?: string; directory?: boolean };

export function buildTree(items: TreeItem[]): TreeNode[] {
    const root: TreeNode[] = [];

    for (const item of items) {
        const rawPath =
            typeof item === "string"
                ? item
                : item?.path;

        if (!rawPath)
            continue;

        const parts = rawPath
            .replace(/\\/g, "/")
            .split("/")
            .filter(Boolean);

        let current = root;
        let currentPath = "";

        for (let i = 0; i < parts.length; i++) {
            const part = parts[i];

            currentPath = currentPath
                ? `${currentPath}/${part}`
                : part;

            let node = current.find(n => n.name === part);

            if (!node) {
                node = {
                    name: part,
                    path: currentPath,
                    directory: i < parts.length - 1,
                    children: []
                };

                current.push(node);
            }

            current = node.children;
        }
    }

    return root;
}