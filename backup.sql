-- MySQL dump 10.13  Distrib 8.0.40, for Linux (x86_64)
--
-- Host: localhost    Database: marzbanbot
-- ------------------------------------------------------
-- Server version	8.0.40-0ubuntu0.22.04.1

/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!50503 SET NAMES utf8mb4 */;
/*!40103 SET @OLD_TIME_ZONE=@@TIME_ZONE */;
/*!40103 SET TIME_ZONE='+00:00' */;
/*!40014 SET @OLD_UNIQUE_CHECKS=@@UNIQUE_CHECKS, UNIQUE_CHECKS=0 */;
/*!40014 SET @OLD_FOREIGN_KEY_CHECKS=@@FOREIGN_KEY_CHECKS, FOREIGN_KEY_CHECKS=0 */;
/*!40101 SET @OLD_SQL_MODE=@@SQL_MODE, SQL_MODE='NO_AUTO_VALUE_ON_ZERO' */;
/*!40111 SET @OLD_SQL_NOTES=@@SQL_NOTES, SQL_NOTES=0 */;

--
-- Table structure for table `alembic_version`
--

DROP TABLE IF EXISTS `alembic_version`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `alembic_version` (
  `version_num` varchar(32) NOT NULL,
  PRIMARY KEY (`version_num`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `alembic_version`
--

LOCK TABLES `alembic_version` WRITE;
/*!40000 ALTER TABLE `alembic_version` DISABLE KEYS */;
INSERT INTO `alembic_version` VALUES ('36159a9e6985');
/*!40000 ALTER TABLE `alembic_version` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `crypto_payments`
--

DROP TABLE IF EXISTS `crypto_payments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `crypto_payments` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tg_id` bigint DEFAULT NULL,
  `lang` varchar(64) DEFAULT NULL,
  `payment_uuid` varchar(64) DEFAULT NULL,
  `order_id` varchar(64) DEFAULT NULL,
  `chat_id` bigint DEFAULT NULL,
  `callback` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `crypto_payments`
--

LOCK TABLES `crypto_payments` WRITE;
/*!40000 ALTER TABLE `crypto_payments` DISABLE KEYS */;
/*!40000 ALTER TABLE `crypto_payments` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `vpnusers`
--

DROP TABLE IF EXISTS `vpnusers`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `vpnusers` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tg_id` bigint DEFAULT NULL,
  `vpn_id` varchar(64) DEFAULT NULL,
  `test` tinyint(1) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=27 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `vpnusers`
--

LOCK TABLES `vpnusers` WRITE;
/*!40000 ALTER TABLE `vpnusers` DISABLE KEYS */;
INSERT INTO `vpnusers` VALUES (1,84078787,'955963ec92d7871d5fac4d2811248a77',1),(2,7191371256,'93e120abce17760106df48fedfb44c4a',1),(3,5686471972,'62d6db10bb62d5274708f3eed5fd34b1',1),(4,285853656,'971e49080f7aa23b8d709c38d1f234d3',1),(5,729792167,'eb6e674c5bb5304ac75cff60f8e36261',1),(6,272512384,'283f5aab9062f6b504b6e41f845a1e7e',1),(7,1054981153,'e1cfffacca5ab237e10d217f9695e06c',1),(8,402422711,'75e7f45f424f70130188707b3f4b44be',1),(9,2085159328,'bd245a8b3462b0efdaf28dfa75c873a0',1),(10,363481248,'b96dc0d667c9bde4735fd3adbc5ccce4',0),(11,619603919,'01a18b3aed6062f1191d98a28ddf6dc6',0),(12,6317865810,'42493a54afc637387d980e064adae8f0',1),(13,5929139251,'148620ef3f62cbb853c6dac1595d629f',1),(14,1884980448,'71b6de29c23a83c1c06f9285647db830',1),(15,628536573,'07fd8db19196448ade2fc97df52a68fd',1),(16,1004901689,'8352c061fb56f532f34e40f69e9f3473',1),(17,1970870687,'928a66341aab132d0555fbdcc4b3cd63',1),(18,1470753122,'077f7f3f4790ab0560cc193b408ecb16',1),(19,516815086,'b28f8dede01199ce59557c300f763505',1),(20,5313216524,'a9c1fd5a7cc8c2854e706a3b12479839',1),(21,250427245,'1b79873a3bb54bc2274c3dfb9f1f5769',0),(22,1849112306,'ae8fda8a0f449dca881cce0e9fe92a99',1),(23,498646329,'ac7ffb250ce36cd3b4dc2035d20935ba',1),(24,363505759,'1468b8e6c7c016abdd5796cccd74cedb',1),(25,140022002,'57a70d315fcd62cf39476ac90aa672d8',1),(26,938848181,'1cfef85415c29c731e9de84e37a331ed',0);
/*!40000 ALTER TABLE `vpnusers` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `yookassa_payments`
--

DROP TABLE IF EXISTS `yookassa_payments`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `yookassa_payments` (
  `id` bigint NOT NULL AUTO_INCREMENT,
  `tg_id` bigint DEFAULT NULL,
  `lang` varchar(64) DEFAULT NULL,
  `payment_id` varchar(64) DEFAULT NULL,
  `chat_id` bigint DEFAULT NULL,
  `callback` varchar(64) DEFAULT NULL,
  PRIMARY KEY (`id`),
  UNIQUE KEY `id` (`id`)
) ENGINE=InnoDB AUTO_INCREMENT=28 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `yookassa_payments`
--

LOCK TABLES `yookassa_payments` WRITE;
/*!40000 ALTER TABLE `yookassa_payments` DISABLE KEYS */;
INSERT INTO `yookassa_payments` VALUES (6,84078787,'ru','2eda9ac5-000f-5000-9000-10f3b57db715',84078787,'Shadowpath'),(7,84078787,'ru','2eda9aee-000f-5000-a000-1f62ceca868d',84078787,'Shadowpath'),(8,84078787,'ru','2eda9b43-000f-5000-9000-1a7ce1ebb8a3',84078787,'Shadowpath'),(9,84078787,'ru','2eda9b67-000f-5000-b000-18155362286c',84078787,'Shadowpath'),(19,1054981153,'ru','2eefd7b7-000f-5000-b000-1169960a72dd',1054981153,'Shadowpath'),(20,2085159328,'ru','2f0907c0-000f-5000-b000-1c35bcb0ac57',2085159328,'Shadowpath'),(21,1970870687,'ru','2f0da381-000f-5000-8000-14d6edba3719',1970870687,'Shadowpath'),(25,363505759,'ru','2f2f456f-000f-5000-b000-14527a051d58',363505759,'Shadowpath');
/*!40000 ALTER TABLE `yookassa_payments` ENABLE KEYS */;
UNLOCK TABLES;
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2025-02-25 13:20:33
