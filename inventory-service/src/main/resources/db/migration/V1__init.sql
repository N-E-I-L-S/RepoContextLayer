CREATE TABLE `t_inventory`(
    `id` bigint(20) NOT NULL  AUTO_INCREMENT,
    `quantity` int(11) DEFAULT NULL,
    `sku_code` varchar(255) DEFAULT NULL,
    PRIMARY KEY (`id`)
);