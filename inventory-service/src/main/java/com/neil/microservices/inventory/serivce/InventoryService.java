package com.neil.microservices.inventory.serivce;

import com.neil.microservices.inventory.model.Inventory;
import com.neil.microservices.inventory.repository.InventoryRepository;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

@Service
public class InventoryService {

    @Autowired
    private InventoryRepository inventoryRepository;

    public boolean isInStock(String skuCode, Integer quantity){
        if(skuCode==null || quantity == null)
            throw new RuntimeException("SKU Code or quantity or both missing");
        return inventoryRepository.existsBySkuCodeAndQuantityIsGreaterThanEqual(skuCode, quantity);
    }

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
}
