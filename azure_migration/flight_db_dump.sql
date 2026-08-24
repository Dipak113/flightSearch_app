-- MySQL dump 10.13  Distrib 8.0.42, for Win64 (x86_64)
--
-- Host: localhost    Database: flight_db
-- ------------------------------------------------------
-- Server version	8.0.42

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
-- Current Database: `flight_db`
--

CREATE DATABASE /*!32312 IF NOT EXISTS*/ `flight_db` /*!40100 DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_0900_ai_ci */ /*!80016 DEFAULT ENCRYPTION='N' */;

USE `flight_db`;

--
-- Table structure for table `airports`
--

DROP TABLE IF EXISTS `airports`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `airports` (
  `airport_id` int NOT NULL AUTO_INCREMENT,
  `iata_code` varchar(10) NOT NULL,
  `airport_name` varchar(100) NOT NULL,
  PRIMARY KEY (`airport_id`),
  UNIQUE KEY `iata_code` (`iata_code`)
) ENGINE=InnoDB AUTO_INCREMENT=12 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `airports`
--

LOCK TABLES `airports` WRITE;
/*!40000 ALTER TABLE `airports` DISABLE KEYS */;
INSERT INTO `airports` VALUES (1,'PNQ','Pune International Airport'),(2,'BOM','Chhatrapati Shivaji Maharaj International Airport'),(3,'DEL','Indira Gandhi International Airport'),(4,'BLR','Kempegowda International Airport'),(5,'HYD','Rajiv Gandhi International Airport'),(6,'GOI','Goa International Airport'),(7,'MAA','Chennai International Airport'),(8,'CCU','Netaji Subhas Chandra Bose International Airport'),(9,'HYK','PUNE AIRPORT'),(10,'KJL','KOCHI');
/*!40000 ALTER TABLE `airports` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `flights`
--

DROP TABLE IF EXISTS `flights`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `flights` (
  `flight_id` int NOT NULL AUTO_INCREMENT,
  `search_id` int NOT NULL,
  `airline` varchar(100) NOT NULL,
  `departure_airport` varchar(10) NOT NULL,
  `arrival_airport` varchar(10) NOT NULL,
  `departure_time` datetime NOT NULL,
  `arrival_time` datetime NOT NULL,
  `duration_minutes` int NOT NULL,
  `price` decimal(10,2) NOT NULL,
  PRIMARY KEY (`flight_id`),
  KEY `fk_flight_search` (`search_id`),
  CONSTRAINT `fk_flight_search` FOREIGN KEY (`search_id`) REFERENCES `searches` (`search_id`)
) ENGINE=InnoDB AUTO_INCREMENT=20 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `flights`
--

LOCK TABLES `flights` WRITE;
/*!40000 ALTER TABLE `flights` DISABLE KEYS */;
INSERT INTO `flights` VALUES (1,1,'IndiGo','PNQ','BOM','2026-09-01 06:30:00','2026-09-01 07:35:00',65,3500.00),(2,1,'Air India','PNQ','BOM','2026-09-01 09:00:00','2026-09-01 10:10:00',70,4200.00),(3,1,'Akasa Air','PNQ','BOM','2026-09-01 14:30:00','2026-09-01 15:35:00',65,3800.00),(4,2,'IndiGo','PNQ','DEL','2026-09-05 06:00:00','2026-09-05 08:05:00',125,6500.00),(5,2,'Air India','PNQ','DEL','2026-09-05 11:30:00','2026-09-05 13:40:00',130,7200.00),(6,2,'Vistara','PNQ','DEL','2026-09-05 18:00:00','2026-09-05 20:10:00',130,7800.00),(7,3,'IndiGo','BOM','BLR','2026-09-10 07:00:00','2026-09-10 08:35:00',95,4500.00),(8,3,'Air India','BOM','BLR','2026-09-10 12:30:00','2026-09-10 14:10:00',100,5200.00),(9,3,'Akasa Air','BOM','BLR','2026-09-10 19:00:00','2026-09-10 20:35:00',95,4800.00),(10,4,'IndiGo','PNQ','GOI','2026-09-15 08:00:00','2026-09-15 09:15:00',75,3200.00),(11,4,'Air India','PNQ','GOI','2026-09-15 13:00:00','2026-09-15 14:20:00',80,3900.00),(12,4,'SpiceJet','PNQ','GOI','2026-09-15 18:30:00','2026-09-15 19:45:00',75,3000.00),(13,5,'IndiGo','DEL','HYD','2026-09-20 06:30:00','2026-09-20 08:45:00',135,6000.00),(14,5,'Air India','DEL','HYD','2026-09-20 11:00:00','2026-09-20 13:20:00',140,6800.00),(15,5,'Vistara','DEL','HYD','2026-09-20 17:30:00','2026-09-20 19:50:00',140,7500.00),(16,5,'PUNE AIPORT','HYK','GOI','2026-08-20 18:08:00','2026-08-20 18:08:00',5,500.00),(17,5,'IndiGo','DEL','HYD','2026-09-20 12:20:00','2026-09-20 16:45:00',265,7014.00),(18,5,'IndiGo','DEL','HYD','2026-09-20 12:20:00','2026-09-20 16:45:00',265,7014.00);
/*!40000 ALTER TABLE `flights` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Table structure for table `searches`
--

DROP TABLE IF EXISTS `searches`;
/*!40101 SET @saved_cs_client     = @@character_set_client */;
/*!50503 SET character_set_client = utf8mb4 */;
CREATE TABLE `searches` (
  `search_id` int NOT NULL AUTO_INCREMENT,
  `source_airport_id` int NOT NULL,
  `destination_airport_id` int NOT NULL,
  `travel_date` date NOT NULL,
  `search_timestamp` timestamp NULL DEFAULT CURRENT_TIMESTAMP,
  PRIMARY KEY (`search_id`),
  KEY `fk_search_source_airport` (`source_airport_id`),
  KEY `fk_search_destination_airport` (`destination_airport_id`),
  CONSTRAINT `fk_search_destination_airport` FOREIGN KEY (`destination_airport_id`) REFERENCES `airports` (`airport_id`),
  CONSTRAINT `fk_search_source_airport` FOREIGN KEY (`source_airport_id`) REFERENCES `airports` (`airport_id`)
) ENGINE=InnoDB AUTO_INCREMENT=10 DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_0900_ai_ci;
/*!40101 SET character_set_client = @saved_cs_client */;

--
-- Dumping data for table `searches`
--

LOCK TABLES `searches` WRITE;
/*!40000 ALTER TABLE `searches` DISABLE KEYS */;
INSERT INTO `searches` VALUES (1,1,2,'2026-09-01','2026-08-19 15:02:28'),(2,1,3,'2026-09-05','2026-08-19 15:02:28'),(3,2,4,'2026-09-10','2026-08-19 15:02:28'),(4,1,6,'2026-09-15','2026-08-19 15:02:28'),(5,3,5,'2026-09-20','2026-08-19 15:02:28'),(6,6,5,'2026-08-18','2026-08-19 15:39:28'),(8,4,8,'2026-08-21','2026-08-21 13:23:43'),(9,4,6,'2026-08-21','2026-08-21 13:41:27');
/*!40000 ALTER TABLE `searches` ENABLE KEYS */;
UNLOCK TABLES;

--
-- Dumping routines for database 'flight_db'
--
/*!40103 SET TIME_ZONE=@OLD_TIME_ZONE */;

/*!40101 SET SQL_MODE=@OLD_SQL_MODE */;
/*!40014 SET FOREIGN_KEY_CHECKS=@OLD_FOREIGN_KEY_CHECKS */;
/*!40014 SET UNIQUE_CHECKS=@OLD_UNIQUE_CHECKS */;
/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
/*!40111 SET SQL_NOTES=@OLD_SQL_NOTES */;

-- Dump completed on 2026-08-23 23:30:54
