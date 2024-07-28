#coding

- Important before releasing to production

## Static Files
- Files without Python code
- Images, CSS or JavaScript Code
- Don't need a lot of resources to run -> can be cached with proxies and CDNs

### Proxy chaching
- A server as an intermediary between user and provider of web content, 
- Instead of the server, proxies respond to requests of the user 
- Faster, more reliable
- **CDN**: Content Delivery Network, used for proxy caching, ?

## Dynamic Files
- Code must be evaluated on each request -> expensive to run