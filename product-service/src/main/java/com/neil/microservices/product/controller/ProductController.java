package com.neil.microservices.product.controller;


import com.neil.microservices.product.dto.ProductRequest;
import com.neil.microservices.product.dto.ProductResponse;
import com.neil.microservices.product.service.ProductService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.web.bind.annotation.*;

import java.util.List;

@RestController
@RequestMapping("/api/product")
public class ProductController {

    @Autowired
    ProductService productService;

    @PostMapping("")
    public ProductResponse createProduct(@RequestBody ProductRequest product){
        return productService.createProduct(product);
    }

    @GetMapping("")
    public List<ProductResponse> getAllProducts(){
        return productService.getAllProducts();
    }
}
