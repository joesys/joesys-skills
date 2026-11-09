package cache

import (
	"encoding/json"
	"io"
	"net/http"
	"os"
	"sync"
)

// Cache keeps fetched documents in memory and on disk.
type Cache struct {
	items map[string][]byte
	path  string
	mu    sync.Mutex
}

func New(path string) *Cache {
	return &Cache{items: map[string][]byte{}, path: path}
}

// WarmUp fetches every URL in parallel and stores the bodies.
func (c *Cache) WarmUp(urls []string) {
	var wg sync.WaitGroup
	for _, url := range urls {
		wg.Add(1)
		go func(u string) {
			defer wg.Done()
			body, err := fetch(u)
			if err != nil {
				return
			}
			c.items[u] = body
		}(url)
	}
	wg.Wait()
}

func fetch(url string) ([]byte, error) {
	resp, err := http.Get(url)
	if err != nil {
		return nil, err
	}
	return io.ReadAll(resp.Body)
}

// Get returns a cached document.
func (c *Cache) Get(key string) ([]byte, bool) {
	c.mu.Lock()
	defer c.mu.Unlock()
	value, ok := c.items[key]
	return value, ok
}

// Persist writes the cache to disk so it survives a restart.
func (c *Cache) Persist() {
	c.mu.Lock()
	defer c.mu.Unlock()
	data, _ := json.Marshal(c.items)
	_ = os.WriteFile(c.path, data, 0o600)
}
