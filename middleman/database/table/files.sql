-- phpMyAdmin SQL Dump
-- version 5.2.1
-- https://www.phpmyadmin.net/
--
-- Host: 127.0.0.1:3307
-- Generation Time: Nov 23, 2024 at 02:37 PM
-- Server version: 10.4.32-MariaDB
-- PHP Version: 8.2.12

SET SQL_MODE = "NO_AUTO_VALUE_ON_ZERO";
START TRANSACTION;
SET time_zone = "+00:00";


/*!40101 SET @OLD_CHARACTER_SET_CLIENT=@@CHARACTER_SET_CLIENT */;
/*!40101 SET @OLD_CHARACTER_SET_RESULTS=@@CHARACTER_SET_RESULTS */;
/*!40101 SET @OLD_COLLATION_CONNECTION=@@COLLATION_CONNECTION */;
/*!40101 SET NAMES utf8mb4 */;

--
-- Database: `database_pbl4`
--

-- --------------------------------------------------------

--
-- Table structure for table `files`
--

CREATE TABLE `files` (
  `id` int(11) NOT NULL,
  `victim_id` int(11) NOT NULL,
  `file_name` varchar(255) DEFAULT NULL,
  `file_path` text DEFAULT NULL,
  `uploaded_at` datetime DEFAULT NULL
) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4 COLLATE=utf8mb4_general_ci;

--
-- Dumping data for table `files`
--

INSERT INTO `files` (`id`, `victim_id`, `file_name`, `file_path`, `uploaded_at`) VALUES
(4, 1, 'Keylog.txt', 'received_files\\Keylog.txt', '2024-11-23 12:08:30'),
(5, 1, 'record.wav', 'received_files\\record.wav', '2024-11-23 12:08:30'),
(6, 1, 'wifis.txt', 'received_files\\wifis.txt', '2024-11-23 12:08:30'),
(7, 3, 'Keylog.txt', 'received_files\\Keylog.txt', '2024-11-23 12:44:08'),
(8, 3, 'record.wav', 'received_files\\record.wav', '2024-11-23 12:44:08'),
(9, 3, 'wifis.txt', 'received_files\\wifis.txt', '2024-11-23 12:44:08'),
(10, 1, 'Keylog.txt', 'received_files1\\Keylog.txt', '2024-11-23 12:56:34'),
(11, 1, 'record.wav', 'received_files1\\record.wav', '2024-11-23 12:56:37'),
(12, 1, 'wifis.txt', 'received_files1\\wifis.txt', '2024-11-23 12:56:37'),
(13, 3, 'Keylog.txt', 'received_files3\\Keylog.txt', '2024-11-23 12:59:37'),
(14, 3, 'record.wav', 'received_files3\\record.wav', '2024-11-23 12:59:41'),
(15, 3, 'wifis.txt', 'received_files3\\wifis.txt', '2024-11-23 12:59:41'),
(16, 3, 'Keylog.txt', 'received_files\\3\\Keylog.txt', '2024-11-23 13:05:13'),
(17, 3, 'Keylog.txt', 'middleman/received_files\\3\\Keylog.txt', '2024-11-23 13:07:17'),
(18, 1, 'Keylog.txt', 'middleman/received_files\\1\\Keylog.txt', '2024-11-23 13:08:58'),
(19, 3, 'Keylog.txt', 'PBL4-Keylogger-BotNet/middleman/received_files\\3\\Keylog.txt', '2024-11-23 13:10:54'),
(20, 3, 'Keylog.txt', 'PBL4-Keylogger-BotNet/middleman/received_files\\3\\Keylog.txt', '2024-11-23 13:16:13'),
(21, 1, 'Keylog.txt', 'PBL4-Keylogger-BotNet/middleman/received_files\\1\\Keylog.txt', '2024-11-23 13:21:52'),
(22, 1, 'record.wav', 'PBL4-Keylogger-BotNet/middleman/received_files\\1\\record.wav', '2024-11-23 13:21:52'),
(23, 1, 'wifis.txt', 'PBL4-Keylogger-BotNet/middleman/received_files\\1\\wifis.txt', '2024-11-23 13:21:52'),
(24, 3, 'Keylog.txt', 'PBL4-Keylogger-BotNet/middleman/received_files\\3\\Keylog.txt', '2024-11-23 13:26:40'),
(25, 3, 'record.wav', 'PBL4-Keylogger-BotNet/middleman/received_files\\3\\record.wav', '2024-11-23 13:26:42'),
(26, 3, 'wifis.txt', 'PBL4-Keylogger-BotNet/middleman/received_files\\3\\wifis.txt', '2024-11-23 13:26:42'),
(27, 4, 'Keylog.txt', 'PBL4-Keylogger-BotNet/middleman/received_files\\4\\Keylog.txt', '2024-11-23 14:36:51'),
(28, 4, 'record.wav', 'PBL4-Keylogger-BotNet/middleman/received_files\\4\\record.wav', '2024-11-23 14:36:51'),
(29, 4, 'wifis.txt', 'PBL4-Keylogger-BotNet/middleman/received_files\\4\\wifis.txt', '2024-11-23 14:36:51'),
(30, 4, 'Keylog.txt', 'PBL4-Keylogger-BotNet/middleman/received_files\\4\\Keylog.txt', '2024-11-23 15:11:52'),
(31, 4, 'record.wav', 'PBL4-Keylogger-BotNet/middleman/received_files\\4\\record.wav', '2024-11-23 15:11:53'),
(32, 4, 'wifis.txt', 'PBL4-Keylogger-BotNet/middleman/received_files\\4\\wifis.txt', '2024-11-23 15:11:53'),
(33, 4, 'Keylog.txt', 'PBL4-Keylogger-BotNet/middleman/received_files\\4\\Keylog.txt', '2024-11-23 15:19:26'),
(34, 4, 'record.wav', 'PBL4-Keylogger-BotNet/middleman/received_files\\4\\record.wav', '2024-11-23 15:19:26'),
(35, 4, 'wifis.txt', 'PBL4-Keylogger-BotNet/middleman/received_files\\4\\wifis.txt', '2024-11-23 15:19:26'),
(36, 4, 'Keylog.txt', 'PBL4-Keylogger-BotNet/middleman/received_files\\4\\Keylog.txt', '2024-11-23 15:24:38'),
(37, 4, 'record.wav', 'PBL4-Keylogger-BotNet/middleman/received_files\\4\\record.wav', '2024-11-23 15:24:38'),
(38, 4, 'wifis.txt', 'PBL4-Keylogger-BotNet/middleman/received_files\\4\\wifis.txt', '2024-11-23 15:24:39'),
(39, 4, 'Keylog.txt', 'PBL4-Keylogger-BotNet/middleman/received_files\\4\\Keylog.txt', '2024-11-23 16:23:24'),
(40, 4, 'record.wav', 'PBL4-Keylogger-BotNet/middleman/received_files\\4\\record.wav', '2024-11-23 16:23:24'),
(41, 4, 'wifis.txt', 'PBL4-Keylogger-BotNet/middleman/received_files\\4\\wifis.txt', '2024-11-23 16:23:24');

--
-- Indexes for dumped tables
--

--
-- Indexes for table `files`
--
ALTER TABLE `files`
  ADD PRIMARY KEY (`id`),
  ADD KEY `victim_id` (`victim_id`);

--
-- AUTO_INCREMENT for dumped tables
--

--
-- AUTO_INCREMENT for table `files`
--
ALTER TABLE `files`
  MODIFY `id` int(11) NOT NULL AUTO_INCREMENT, AUTO_INCREMENT=42;

--
-- Constraints for dumped tables
--

--
-- Constraints for table `files`
--
ALTER TABLE `files`
  ADD CONSTRAINT `files_ibfk_1` FOREIGN KEY (`victim_id`) REFERENCES `victims` (`id`);
COMMIT;

/*!40101 SET CHARACTER_SET_CLIENT=@OLD_CHARACTER_SET_CLIENT */;
/*!40101 SET CHARACTER_SET_RESULTS=@OLD_CHARACTER_SET_RESULTS */;
/*!40101 SET COLLATION_CONNECTION=@OLD_COLLATION_CONNECTION */;
