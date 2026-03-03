package com.neil.microservices.inventory.controller;

import com.neil.microservices.inventory.dto.UpdateQuantityRequest;
import com.neil.microservices.inventory.serivce.InventoryService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

@RestController
@RequestMapping("/api/inventory")
public class InventoryController {

    @Autowired
    private InventoryService inventoryService;

    @GetMapping
    public boolean isInStock(@RequestParam String skuCode, @RequestParam Integer quantity){
        return inventoryService.isInStock(skuCode, quantity);
    }

    @PatchMapping
    public boolean updateQuantity(@RequestBody UpdateQuantityRequest request){
        return inventoryService.updateQuantity(request.skuCode(), request.quantity());
    }

}
