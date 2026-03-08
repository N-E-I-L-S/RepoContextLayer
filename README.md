# ContextLayer – Repository Intelligence Engine

ContextLayer is a static analysis + semantic search + dependency graph engine for Java microservices.

It parses Java repositories, extracts structural information (classes, methods, fields), builds dependency graphs, generates semantic embeddings, and enables intelligent code retrieval for LLM-powered workflows.

This project is designed for use cases like:

- “Write a loader for `User.email`”
- “Find all writers of `Order.status`”
- “Show all methods dependent on this attribute”
- “Generate service layer for this entity”
- “Expand dependencies of this method across microservices”

---

# Architecture Overview

### Code structure graph and semantic embedding generation:

```
                    Java Repository
                          ↓
                    Scan Java Files
                          ↓
                    Extract Imports
                          ↓
        ┌────────── Parse Java Files ──────────────┐
        ↓                                          |
    Build Class Index                              |
        ↓                                          |
Resolve Dependency Injection                       |
      & Types                                      |
        ↓                                          ↓
┌───────────────────────────────┬───────────────────────────────┐
│                               │                               │
│        Build Call Graph       │        Generate Embeddings    │
│                               │                               │
└───────────────────────────────┴───────────────────────────────┘
```

### Resolving User query

```
                User query 
                    ↓
            Semantic embedding
                    ↓
        Retrieve relevant documents
                    ↓
    Graph expansion using call graph
                    ↓
        Relevant files and indices
                    ↓
            Relevant Code snippets

## Sample
### Input Query - "change return type of placeOrder to return boolean"
### Output Code snippets :
=== Extracted Code Snippets ===


--- (order-service\src\main\java\com\neil\microservices\order\service\OrderService.java:30-59) ---  
    
    public void placeOrder(OrderRequest orderRequest){
       boolean productInStock = inventoryClient.isInStock(orderRequest.skuCode(), orderRequest.quantity());
       if(productInStock) {
            Order order = new Order();

            order.setOrderNumber(UUID.randomUUID().toString());
            order.setPrice(orderRequest.price());
            order.setSkuCode(orderRequest.skuCode());
            order.setQuantity(orderRequest.quantity());
            orderRepository.save(order);

            OrderPlacedEvent orderPlacedEvent = new OrderPlacedEvent(orderRequest.userDetails().email(),order.getOrderNumber());
            System.out.println(orderPlacedEvent);
            kafkaTemplate.send("order_placed", orderPlacedEvent);
            log.info("Order {} sent to kafka topic order_placed", orderPlacedEvent);

           InventoryOrderClientRequest updateQuantityRequest = new InventoryOrderClientRequest(orderRequest.skuCode(), orderRequest.quantity());
           boolean inventoryUpdated = inventoryClient.updateQuantity(updateQuantityRequest);        

            if(inventoryUpdated){
                log.info("Inventory for product with skuCode {} has been updated for order placed", orderRequest.skuCode());
            }
            else{
                throw new RuntimeException("Inventory could not be updated for current order");     
            }
       }
       else{
           throw  new RuntimeException("Product with skuCode "+ orderRequest.skuCode()+" is not in stock");
       }
    }


--- (order-service\src\main\java\com\neil\microservices\order\controller\OrderController.java:15-25) ---
    
    @PostMapping
    public String placeOrder(@RequestBody OrderRequest orderRequest){
        try{
            orderService.placeOrder(orderRequest);
            return "Order Placed Successfully";
        }
        catch (Exception e){
            System.out.println("An Error Occurred");
            throw e;
        }
    }


--- (inventory-service\src\main\java\com\neil\microservices\inventory\serivce\InventoryService.java:14-18) ---
    
    public boolean isInStock(String skuCode, Integer quantity){
        if(skuCode==null || quantity == null)
            throw new RuntimeException("SKU Code or quantity or both missing");
        return inventoryRepository.existsBySkuCodeAndQuantityIsGreaterThanEqual(skuCode, quantity); 
    }


--- (inventory-service\src\main\java\com\neil\microservices\inventory\controller\InventoryController.java:15-18) ---
    
    @GetMapping
    public boolean isInStock(@RequestParam String skuCode, @RequestParam Integer quantity){
        return inventoryService.isInStock(skuCode, quantity);
    }


--- (inventory-service\src\main\java\com\neil\microservices\inventory\serivce\InventoryService.java:20-31) ---
    
    public boolean updateQuantity(String skuCode, Integer quantity){
        Inventory inventory = inventoryRepository.findBySkuCode(skuCode)
                .orElseThrow(() -> new RuntimeException("Product not found with SKU code: " + skuCode));

        if (inventory.getQuantity() >= quantity) {
            inventory.setQuantity(inventory.getQuantity() - quantity);
            inventoryRepository.save(inventory);
            return true;
        } else {
            return false;
        }
    }


## To Do:
Implement BM25 for keyword matching