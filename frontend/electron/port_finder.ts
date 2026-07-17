import net from 'net';

/**
 * Find a free TCP port starting from the given port number.
 */
export function findFreePort(startPort: number, maxAttempts = 100): Promise<number> {
    return new Promise((resolve, reject) => {
        const server = net.createServer();
        server.listen(startPort, '127.0.0.1', () => {
            const port = (server.address() as net.AddressInfo).port;
            server.close(() => resolve(port));
        });
        server.on('error', () => {
            // Port is in use, try next
            findFreePort(startPort + 1, maxAttempts - 1)
                .then(resolve)
                .catch(reject);
        });
    });
}
